# Next-Generation AI (Trustworthy GenAI): DIA5-G5

- DIA class: **DIA5**
- Sub-group: **DIA5-G5**
- Members: Kerry Assohoun, Sam Olivares, Etienne Padelo, Armand Bussolino, Shayan Karimi

ESILV A4, module Next-Generation AI, 2026-27. Repository shared by the sub-group from TD 1 to TD 3.

## Sub-group

| Role (TD 1) | Member | Task |
|---|---|---|
| A | Kerry | Groq, `openai/gpt-oss-120b` |
| B | Sam | Groq, `openai/gpt-oss-20b` |
| C | Etienne | OpenRouter, `cohere/north-mini-code:free`; consolidates references, traces and summaries |
| D | Armand | Groq, `qwen/qwen3.8-27b` |
| E | Shayan | OpenRouter, `dots-studio/dots-3-note-preview:free` |

Five members: the protocol's F-H role (cross-checking, merging, summaries) is shared, each operator cross-checking another's references (A-B, C-D, E-A).

Instructor: Paul Gabriel. Roles rotate in TD 2 and TD 3.

## Pack and data

- Pack: `2026-10-14-students-1` (original kit README: [README-kit.md](README-kit.md))
- Database: `data/boutique.sqlite`, SHA-256 `0077e235adc2ca647b484e3083c98a6d7cae3ef3655ce366a299caf13398fec2` (seed 20260925, as in `data/manifest.json`)
- Authorised models: `modeles-autorises.json` dated 2026-10-14

## Environment

Python 3.10 or later (tested with 3.14), a virtual environment and `requests`. On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install requests
python verify-data.py
python check_access.py --no-network
```

API keys are personal and live only in environment variables (`GROQ_API_KEY`, `OPENROUTER_API_KEY`). No key, `.env` file or credential screenshot is ever committed (see `.gitignore`).

## Commands

Each operator ran their model on the twenty questions with their own state and trace files (calls need the key of the matching provider):

```powershell
python skeleton-multi-llm-en.py --run --models groq:openai/gpt-oss-120b --state state-A.jsonl --out traces-A.csv
python skeleton-multi-llm-en.py --run --models groq:openai/gpt-oss-20b --state state-B.jsonl --out traces-B.csv
python skeleton-multi-llm-en.py --run --models openrouter:cohere/north-mini-code:free --state state-C.jsonl --out traces-C.csv
python skeleton-multi-llm-en.py --run --models groq:qwen/qwen3.8-27b --state state-D.jsonl --out traces-D.csv
python skeleton-multi-llm-en.py --run --models openrouter:dots-studio/dots-3-note-preview:free --state state-E.jsonl --out traces-E.csv
```

Replaying the results offline, without any key or network call:

```powershell
python merge_traces.py                          # state-A..E.jsonl -> traces-td1.jsonl, checked against traces-td1.csv and the comparison table
python skeleton-multi-llm-en.py --rates         # correct answers per model, from traces-td1.jsonl
python skeleton-multi-llm-en.py --replay traces-td1.jsonl --state traces-replay.jsonl --out traces-replay.csv   # re-runs every stored SQL on the local base
```

## TD 1 files

| File | Content |
|---|---|
| `reference-td1.csv` | the twenty reference queries and values, author and cross-checker of each |
| `reference-A.csv`, `reference-B-temp.csv`, `reference-C.csv` (+ `refs/`), `reference-D.csv`, `reference_E.csv` | each member's references, before consolidation |
| `check_reference_B.py`, `crosscheck_A_by_B.py`, `validate_role_d.py`, `check_reference_E.py` | the independent checks of the references |
| `traces-<role>.csv`, `state-<role>.jsonl` | raw traces of each operator, every attempt |
| `traces-td1.csv`, `traces-td1.jsonl` | the 103 attempts merged (`merge_traces.py`) |
| `model-question-comparison-en.csv` | final result and cause for each of the 100 cells |
| `five-model-summary-en.csv` | index, dated prices, access and results per family for the five models |
| `prompts-en.md` | system and user prompts verbatim, fingerprint of each question |
| `reports/td1.md` | the session report |

## Status

| Session | Report | Status |
|---|---|---|
| TD 1, 21/10/2026 | [reports/td1.md](reports/td1.md) | done: 20/20 references, 100 cells traced (75 correct, 21 incorrect, 3 invalid SQL, 1 not executed after HTTP 429) |
| TD 2, 18/11/2026 | | |
| TD 3, 11/12/2026 | | |
