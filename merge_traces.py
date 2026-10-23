#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Merge the TD 1 state files of the five operators into `traces-td1.jsonl`,
then check it against `traces-td1.csv` and the comparison table.

    python merge_traces.py           # writes traces-td1.jsonl, prints the checks
    python merge_traces.py --check   # checks only, writes nothing

Every attempt is kept, in the order of the operators (A to E) and of the
calls. The checks: same rows as `traces-td1.csv`, one prompt fingerprint per
question, and every final status of `model-question-comparison-en.csv` equal
to the verdict of the last attempt of its cell.

Standard library only.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATES = [HERE / f"state-{role}.jsonl" for role in "ABCDE"]
OUT_JSONL = HERE / "traces-td1.jsonl"
CSV_MERGED = HERE / "traces-td1.csv"
COMPARISON = HERE / "model-question-comparison-en.csv"


def as_text(value) -> str:
    return "" if value is None else str(value)


def load_states() -> list[dict]:
    records = []
    for path in STATES:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(json.loads(line))
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge the TD 1 state files and check the merged traces.")
    parser.add_argument("--check", action="store_true", help="check only, do not write traces-td1.jsonl")
    args = parser.parse_args()

    records = load_states()
    errors = []

    with CSV_MERGED.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != len(records):
        errors.append(f"{CSV_MERGED.name}: {len(rows)} rows, state files: {len(records)} lines")
    for i, (row, record) in enumerate(zip(rows, records), start=2):
        diff = [k for k in row if as_text(record.get(k)) != row[k]]
        if diff:
            errors.append(f"{CSV_MERGED.name} line {i}: differs on {', '.join(diff)}")

    fingerprints: dict[str, set] = {}
    for record in records:
        fingerprints.setdefault(record["case_id"], set()).add(record["prompt_sha256"])
    errors += [f"{case}: {len(fp)} prompt fingerprints" for case, fp in fingerprints.items() if len(fp) != 1]

    last = {}
    for record in records:
        last[f"{record['provider']}:{record['model_requested']}:{record['case_id']}"] = record
    with COMPARISON.open(encoding="utf-8", newline="") as stream:
        comparison = list(csv.DictReader(stream))
    for row in comparison:
        record = last.get(row["cell_id"])
        if record is None:
            errors.append(f"{row['cell_id']}: no trace")
        elif record["verdict"] != row["status"] or as_text(record["value"]) != row["value_cents"]:
            errors.append(f"{row['cell_id']}: comparison says {row['status']} {row['value_cents']!r}, "
                          f"last attempt says {record['verdict']} {as_text(record['value'])!r}")
    if len(comparison) != len(last):
        errors.append(f"{COMPARISON.name}: {len(comparison)} rows for {len(last)} traced cells")

    print(f"{len(records)} attempts, {len(last)} cells, {len(fingerprints)} questions, "
          f"natures: {sorted({r['nature'] for r in records})}")
    if errors:
        print("\n".join(errors))
        return 1
    print(f"OK: {CSV_MERGED.name} has the same rows; one fingerprint per question; "
          f"{COMPARISON.name} matches the last attempt of every cell")

    if not args.check:
        with OUT_JSONL.open("w", encoding="utf-8", newline="\n") as stream:
            for record in records:
                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"Written: {OUT_JSONL.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
