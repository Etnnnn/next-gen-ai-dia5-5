#!/usr/bin/env python3
"""TD 2, Step 1: 2-of-3 (fixed panel) vs 3-of-5 (all five models) on the stored TD 1 traces.

No network, no key. Uses `Orchestrateur.vote_k_sur_n` from skeleton-multi-llm-en.py
and the same proposal rule as atelier-vote.py: the last CSV row of each panel member
for the question is its last attempt; only a `correct`/`incorrect` row with a value
becomes an `executed` proposal, every other row (or a missing row) is an `error`
that stays in n. The reference is compared only AFTER the decision.

    python td2_vote_table.py                   # Markdown table on stdout
    python td2_vote_table.py --csv vote-td2.csv # also writes the table as CSV
    python td2_vote_table.py --check            # contract checks of vote_k_sur_n
"""
import argparse
import csv
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent

PANEL_3 = [
    ("groq", "openai/gpt-oss-120b"),
    ("openrouter", "cohere/north-mini-code:free"),
    ("groq", "qwen/qwen3.8-27b"),
]
PANEL_5 = PANEL_3 + [
    ("groq", "openai/gpt-oss-20b"),
    ("openrouter", "dots-studio/dots-3-note-preview:free"),
]
SHORT = {
    "openai/gpt-oss-120b": "120b",
    "cohere/north-mini-code:free": "cohere",
    "qwen/qwen3.8-27b": "qwen",
    "openai/gpt-oss-20b": "20b",
    "dots-studio/dots-3-note-preview:free": "dots",
}


def load_vote():
    spec = importlib.util.spec_from_file_location("student_skeleton", HERE / "skeleton-multi-llm-en.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return lambda proposals, k: module.Orchestrateur.vote_k_sur_n(None, proposals, k)


def last_rows(rows, case):
    selected = {}
    for row in rows:  # chronological export: the last row wins
        if row["case_id"] == case and row["nature"] == "real":
            selected[(row["provider"], row["model_requested"])] = row
    return selected


def proposals(selected, panel):
    out = []
    for provider, model in panel:
        row = selected.get((provider, model), {})
        value = row.get("value", "")
        valid = row.get("verdict") in {"correct", "incorrect"} and value not in {None, ""}
        out.append(SimpleNamespace(provider=provider, model_requested=model,
                                   value=int(value) if valid else None,
                                   verdict="executed" if valid else "error"))
    return out


def ballot(selected, panel):
    """Human-readable member list: value, or the TD 1 verdict when it does not vote."""
    parts = []
    for provider, model in panel:
        row = selected.get((provider, model), {})
        valid = row.get("verdict") in {"correct", "incorrect"} and row.get("value") not in {None, ""}
        parts.append(f"{SHORT[model]}={row['value'] if valid else row.get('verdict') or 'missing'}")
    return ", ".join(parts)


def show(decision):
    if decision["consensus"]:
        return f"consensus {decision['value']} ({decision['votes']} votes)"
    return f"abstain (max {decision['votes']})"


def agreement(decision, reference):
    if not decision["consensus"]:
        return "-"
    return "yes" if decision["value"] == reference else "**no**"


def check(vote):
    ok = lambda p, m, v: SimpleNamespace(provider=p, model_requested=m, value=v, verdict="executed")
    err = lambda p, m: SimpleNamespace(provider=p, model_requested=m, value=None, verdict="error")
    a, b, c, d, e = PANEL_5
    cases = [
        ("k too small (k=1 of 3)", lambda: vote([ok(*a, 1), ok(*b, 1), ok(*c, 1)], 1), ValueError),
        ("k too large (k=4 of 3)", lambda: vote([ok(*a, 1), ok(*b, 1), ok(*c, 1)], 4), ValueError),
        ("k=2 of 4 is not strict", lambda: vote([ok(*a, 1), ok(*b, 1), ok(*c, 1), ok(*d, 1)], 2), ValueError),
        ("duplicate pair", lambda: vote([ok(*a, 1), ok(*a, 1), ok(*c, 2)], 2), ValueError),
        ("duplicate pair, one in error", lambda: vote([ok(*a, 1), err(*a), ok(*c, 1)], 2), ValueError),
        ("empty panel", lambda: vote([], 1), ValueError),
    ]
    failures = 0
    for name, call, exc in cases:
        try:
            call()
            print(f"FAIL  {name}: no {exc.__name__}")
            failures += 1
        except exc:
            print(f"ok    {name}: {exc.__name__}")
    expected = [
        ("errors stay in n (1 vote of 3)", vote([ok(*a, 5), err(*b), err(*c)], 2),
         {"consensus": False, "value": None, "votes": 1, "models": []}),
        ("executed but value None does not vote", vote([ok(*a, 5), ok(*b, None), ok(*c, 5)], 2),
         {"consensus": True, "value": 5, "votes": 2, "models": [f"{a[0]}:{a[1]}", f"{c[0]}:{c[1]}"]}),
        ("3-of-5 with two errors", vote([ok(*a, 7), ok(*b, 7), ok(*c, 7), err(*d), err(*e)], 3),
         {"consensus": True, "value": 7, "votes": 3, "models": [f"{p}:{m}" for p, m in (a, b, c)]}),
        ("3-of-5 split 2/2/1 abstains", vote([ok(*a, 7), ok(*b, 7), ok(*c, 8), ok(*d, 8), ok(*e, 9)], 3),
         {"consensus": False, "value": None, "votes": 2, "models": []}),
        ("value 0 is a real value", vote([ok(*a, 0), ok(*b, 0), ok(*c, 1)], 2),
         {"consensus": True, "value": 0, "votes": 2, "models": [f"{a[0]}:{a[1]}", f"{b[0]}:{b[1]}"]}),
    ]
    for name, got, want in expected:
        status = "ok  " if got == want else "FAIL"
        failures += got != want
        print(f"{status}  {name}: {got}")
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--traces", type=Path, default=HERE / "traces-td1.csv")
    parser.add_argument("--references", type=Path, default=HERE / "reference-td1.csv")
    parser.add_argument("--csv", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    vote = load_vote()
    if args.check:
        return 1 if check(vote) else 0

    with args.traces.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    with args.references.open(encoding="utf-8", newline="") as fh:
        refs = {r["case_id"]: int(r["revenue_cents"]) for r in csv.DictReader(fh)}

    table = []
    for case in sorted(refs):
        selected = last_rows(rows, case)
        d3 = vote(proposals(selected, PANEL_3), 2)   # decision first ...
        d5 = vote(proposals(selected, PANEL_5), 3)
        ref = refs[case]                              # ... reference after
        table.append({
            "case_id": case,
            "ballots_5": ballot(selected, PANEL_5),
            "vote_2of3": show(d3), "ref_ok_2of3": agreement(d3, ref),
            "vote_3of5": show(d5), "ref_ok_3of5": agreement(d5, ref),
            "reference": ref,
            "changed": "yes" if (d3["consensus"], d3["value"]) != (d5["consensus"], d5["value"]) else "",
        })

    cols = ["case_id", "ballots_5", "vote_2of3", "ref_ok_2of3", "vote_3of5", "ref_ok_3of5", "reference", "changed"]
    print("| " + " | ".join(cols) + " |")
    print("|" + "---|" * len(cols))
    for r in table:
        print("| " + " | ".join(str(r[c]) for c in cols) + " |")
    if args.csv:
        with args.csv.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            w.writerows(table)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
