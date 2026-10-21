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

```powershell
python skeleton-multi-llm-en.py --run --models groq:openai/gpt-oss-120b --cases C01,C03 --state state-A.jsonl --out traces-A.csv
```

## Status

| Session | Report | Status |
|---|---|---|
| TD 1, 21/10/2026 | [reports/td1.md](reports/td1.md) | in progress |
| TD 2, 18/11/2026 | | |
| TD 3, 11/12/2026 | | |
