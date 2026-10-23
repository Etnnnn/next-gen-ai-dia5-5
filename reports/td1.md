# TD 1 report, 21/10/2026

Sub-group DIA5-G5 (Kerry Assohoun, Sam Olivares, Etienne Padelo, Armand Bussolino, Shayan Karimi), instructor Paul Gabriel. Pack `2026-10-14-students-1`, database `data/boutique.sqlite` (SHA-256 `0077e235…8fec2`, see the README).

## What we did

| Step | Completed | Evidence |
|---|---|---|
| 1. Twenty reference queries, each cross-checked by another member | yes, 20/20 equal to the published values on the first attempt | [`reference-td1.csv`](../reference-td1.csv), `reference-<role>.csv`, check scripts |
| 2. Five models on the twenty questions, one trace line per call | yes, 100 cells, 103 attempts, all real calls | [`traces-td1.csv`](../traces-td1.csv), [`traces-td1.jsonl`](../traces-td1.jsonl), `traces-<role>.csv`, `state-<role>.jsonl` |
| 3. Reading the traces, the two summaries | yes | [`model-question-comparison-en.csv`](../model-question-comparison-en.csv), [`five-model-summary-en.csv`](../five-model-summary-en.csv) |
| Prompts, verbatim | yes, unchanged during the session | [`prompts-en.md`](../prompts-en.md) |

Observed facts (read from the files) and hypotheses about causes are kept apart below; hypotheses are marked as such.

## References

Each member computes the references of their questions in `reference-<role>.csv`, then another member cross-checks them independently (A-B, C-D, E-A, see the README). Each member then fills their own rows of `reference-td1.csv`; C checks the consolidated file.

| Role | Questions | File | Own check | Cross-checked by | Cross-check result |
|---|---|---|---|---|---|
| A | C01, C04, C05, C06 | `reference-A.csv` | | B | match |
| B | C07, C12, C13, C20 | `reference-B-temp.csv` | `check_reference_B.py` | A | match |
| C | C02, C08, C09, C11 | `reference-C.csv`, queries in `refs/` | Python recomputation from `data/*.csv` with a hand-written completed-age function; boundary customers (C001-C007, born one day apart) checked | D | match (same four values) |
| D | C03, C10, C14, C18 | `reference-D.csv` | `validate_role_d.py` | C | match (same four values): C recomputed them blind, with a different SQL age formula (date shifts instead of year/month-day arithmetic) and in Python from `data/*.csv` |
| E | C15, C16, C17, C19 | `reference_E.csv` | `check_reference_E.py` | A | match |

`reference-td1.csv` holds the twenty queries and values, with who wrote and who cross-checked each one (`written_by`, `checked_by`). `reference-B-temp.csv` is B's working file: its queries were given a `COALESCE` in `reference-td1.csv` so that an empty selection returns 0, values unchanged (commit `cb00d5e`).

### Comparison with the published values

The instructor published the twenty reference values on 21/10/2026 during the session ([TD 1: the twenty reference values](https://storage.googleapis.com/docs.g.quanticfactory.io/ESILV/next-generation-ai/latest/students/reference-values-td1-en.html), pack 2026-10-18-students-1). We compared them only after our own computation and cross-checks.

Result: **20/20 identical on the first attempt, no correction needed.** Each value is produced by the query stored next to it in `reference-td1.csv`; re-running all twenty queries on `data/boutique.sqlite` (opened read-only) gives back the stored values.

### Conventions applied

- Period "from S to E": `o.date >= S AND o.date < E`, compared as text on `'YYYY-MM-DD HH:MM:SS'`.
- Completed age on a day D: N years when the N-th anniversary is on or before D and the (N+1)-th after it. In SQL, "exactly 25 on D" is `birth_date <= date(D, '-25 years') AND birth_date > date(D, '-26 years')`. "At the time of the order" (C10, C18) uses the order day: year difference minus 1 when the month-day of the order is before the month-day of birth, `= 25`. C rechecked D's C10 and C18 blind with the date-shift form.
- Revenue: `SUM(quantity_product * price)` in euro cents excluding VAT, `COALESCE(..., 0)` when nothing matches.
- Product list: `o.product_id IN (...)`.

## The calls

- Batch: 100 cells (5 models x 20 questions), **60 Groq and 40 OpenRouter initial calls**, plus 3 retries on Groq: 103 attempts, all `nature = real`. No replayed or simulated line.
- Each operator ran their own model with their own key, one request at a time, through `skeleton-multi-llm-en.py --run` (temperature 0, capped output, 45 s timeout, 3 s pause, at most one retry per cell). Calls between 13:32 and 13:59 UTC (15:32 to 15:59 Paris time).
- The prompt is the same for the five models: `merge_traces.py` checks that each question has **one single `prompt_sha256`** across all 103 attempts, and `prompts-en.md` recomputes the twenty fingerprints from the skeleton's system and user prompts.
- `traces-td1.csv` merges the five raw CSV files under one header; `traces-td1.jsonl` is the same merge of the five `state-<role>.jsonl` files. `python merge_traces.py --check` confirms that the two hold the same rows and that every final status of the comparison table is the verdict of the last attempt of its cell.
- Offline replay (`skeleton-multi-llm-en.py --replay traces-td1.jsonl`, separate `nature = replay` files, not committed) re-executes every stored SQL on the local base. It gives the same verdict for each of the 100 cells, so the results do not depend on the machine that ran the calls.

## Results

Correct answers per model and question family (final verdict of each cell). Families from `questions-td1.json`: period C01, C04-C07, C20; age (on a reference date or at the order) C02, C08-C11; product list C03, C12-C14; combined C15-C19.

| Model (access) | Period | Age | Product | Combined | Total | Other statuses |
|---|---|---|---|---|---|---|
| `openai/gpt-oss-120b` (Groq) | 6/6 | 5/5 | 4/4 | 5/5 | **20/20** | |
| `openai/gpt-oss-20b` (Groq) | 6/6 | 2/5 | 4/4 | 5/5 | **17/20** | |
| `qwen/qwen3.8-27b` (Groq) | 6/6 | 3/5 | 4/4 | 0/5 | **13/20** | C18 `not_executed` (HTTP 429) |
| `dots-studio/dots-3-note-preview:free` (OpenRouter) | 6/6 | 2/5 | 4/4 | 2/5 | **14/20** | C19 `sql_invalid` |
| `cohere/north-mini-code:free` (OpenRouter) | 6/6 | 0/5 | 4/4 | 1/5 | **11/20** | C02, C09 `sql_invalid` |

Over the 100 cells: 75 correct, 21 incorrect, 3 invalid SQL, 1 not executed. Same figures with `python skeleton-multi-llm-en.py --rates`, which reads `traces-td1.jsonl`.

**All 50 period and product cells are correct. All 24 wrong or invalid answers concern a customer's age.** The hardest question is C09 (age 25 on 2026-09-26): only `gpt-oss-120b` gets it right. C02, C10, C17 and C19 are found by two models out of five.

## Causes of failure, read from the traces

Each failed cell has its cause in the `explanation` column of `model-question-comparison-en.csv`, read from the returned SQL or the HTTP status. The causes fall into five kinds.

| Kind | Cells | What the SQL shows |
|---|---|---|
| Age window not shifted by 25 years | 20B C02, C09, C11; Cohere C16, C17 | e.g. 20B C02: `c.birth_date > '2025-09-25' AND c.birth_date <= '2026-09-25'` selects customers aged 0, so the value is 0 instead of 590320 |
| Year difference instead of completed age | Cohere C10; Qwen C10; Dots C10, C17, C18 | only "year difference 25, birthday passed" is kept; customers born the year before whose birthday is still to come are missed |
| One-day boundary error | Qwen C16, C17 | strict `<` vs `<=` on month-day: C001 (25 on 2026-09-25) excluded, C004 (26 that day) included |
| Filter that selects the wrong customers (always true, always false, too broad or too narrow) | Cohere C08, C11, C15, C19; Qwen C09, C15, C19; Dots C02, C09 | e.g. Qwen C19 compares a year with a full date, `strftime('%Y', date(c.birth_date, '+25 years')) <= '2026-09-25'`, true for every customer: 83580 (all product d sales of September) instead of 1990 |
| Invalid SQL | Cohere C02, C09; Dots C19 | Cohere puts a column alias inside `WHERE` (`CAST(...) AS INTEGER) AS age_year`); Dots misplaces a parenthesis in `CAST((strftime(...) AS INTEGER) - ...)`. SQLite: `syntax error near "AS"` |

Hypothesis, not tested: the prompt states the completed-age convention in words but gives no SQL pattern for it, and each model writes its own date arithmetic; the period and product conventions translate directly into one SQL condition.

### A failed access is not a wrong answer

`groq:qwen/qwen3.8-27b:C18` is the only cell without an answer. Its two attempts (13:46:26 and 13:46:34 UTC) return **HTTP 429**: `Rate limit reached for model qwen/qwen3.8-27b ... on output tokens per minute (OTPM): Limit 1000, Used 949, Requested 175` (second attempt: `Used 814, Requested 233`). Each refusal comes back in under 100 ms, with no `model_returned`, no SQL, no value and no token count. The model never received the question, so this cell says nothing about Qwen's ability on C18: its status is `not_executed`, not `incorrect`, and it is left out of the 13/20 of correct answers rather than counted as an error. Under the protocol's single retry, the cell stays unfinished.

Compare with `groq:qwen/qwen3.8-27b:C19`: HTTP 200, a SQL query returned and executed, a value of 83580 against 1990, so a **wrong answer** whose cause can be read from the SQL (filter always true, above).

Observed: the Groq free plan caps Qwen at 1000 output tokens per minute, and our 23 attempts ran at about five per minute, with about 130 output tokens per answer on average. The 429s cluster between 13:46:05 and 13:46:34, on C16, C17 and C18. C16 and C17 succeeded on their retry, after the `Retry-After` delay.

### A trace explained: `groq:qwen/qwen3.8-27b:C16`

Two lines in `traces-td1.csv` (and `traces-D.csv`) for this cell:

| attempts | date_utc | http_status | verdict | value | tokens prompt / completion | latency |
|---|---|---|---|---|---|---|
| 1 | 13:46:05 | 429 | `not_executed` | empty | empty / empty | 50 ms |
| 2 | 13:46:09 | 200 | `incorrect` | 367050 (reference 376740) | 620 / 175 | 780 ms |

- Fingerprint: `ebc89bbcb01e5890…` on both lines, and on the four other models' C16 lines: the same prompt was sent to every model.
- Retry: the first attempt is refused by the rate limit, and the skeleton retries once after the `Retry-After` delay. The final verdict is taken from attempt 2, and both attempts are kept.
- Missing measurements: the tokens of the refused attempt are **empty, not zero**, since nothing was measured. In the same way, `cost_native` is empty on all 63 Groq lines because Groq returns no cost, while it is `0` on the 40 OpenRouter lines, where the `:free` route reports a cost of zero. `tokens_reasoning` is reported by Groq for the two GPT-OSS models, is empty for Qwen, and is 0 on OpenRouter.

### Same wrong value from several models (to read in TD 2)

Two questions get the same wrong value from several models, each through its own SQL:

- **C10**: Cohere, Qwen and Dots all return **119410** (reference 558980). Their three queries differ, but each one only keeps "year difference 25, birthday already passed".
- **C19**: Cohere and Qwen both return **83580** (reference 1990). Both age filters are always true.

Cohere, Qwen and `gpt-oss-120b` make up the fixed TD 2 panel. On C10 and C19, a 2-of-3 vote should therefore keep the wrong value. This will be checked with the implemented vote in TD 2 and is not a result yet.

## What the batch supports for routing (hypothesis)

On this batch only: every model is enough for period and product-list questions, and only `gpt-oss-120b` gets every age question right. The routing hypothesis to test in TD 2 is therefore to send period and product questions to the cheapest model and age questions to `gpt-oss-120b`, or to a quorum. Paid-route prices are in `five-model-summary-en.csv`: gpt-oss-20b at $0.018/$0.09 per million input/output tokens, gpt-oss-120b at $0.15/$0.60, Qwen at $0.04/$1.35. Cohere and Dots have no documented paid route (N/A).

## Limits

- One run of twenty questions per model, at temperature 0: no repetition, so neither an error rate nor a ranking of the models. A second run could return other SQL.
- The questions cover four families on one five-product, 59-customer database. Ten of the twenty questions involve age, which weighs heavily in the totals.
- C18 has no answer from Qwen (HTTP 429): Qwen's 13/20 comes from 19 executed cells.
- Dots is a preview model and may change or be withdrawn. Cohere and Dots were only reachable through a free route, without a public index in the 28/09/2026 portfolio.
- The `error` field is cut at 200 characters by the skeleton (`Please...` truncated): the full 429 message is not kept.
- Each model ran once, on one account; we did not compare two accounts or two moments for the same model.

## Contributions

| Member | Role | Contribution |
|---|---|---|
| Kerry Assohoun | A | References C01, C04-C06; cross-checks of B's and E's references; batch A (`gpt-oss-120b`, Groq) |
| Sam Olivares | B | References C07, C12, C13, C20 and `check_reference_B.py`; independent cross-check of A's references (`crosscheck_A_by_B.py`); batch B (`gpt-oss-20b`, Groq) |
| Etienne Padelo | C | References C02, C08, C09, C11 (`refs/`), blind cross-check of D's references; batch C (`cohere/north-mini-code:free`, OpenRouter); merge of the traces, comparison table, five-model summary, prompts, README and this report |
| Armand Bussolino | D | References C03, C10, C14, C18 and `validate_role_d.py`; cross-check of C's references; batch D (`qwen/qwen3.8-27b`, Groq) |
| Shayan Karimi | E | References C15-C17, C19 and `check_reference_E.py`; batch E (`dots-3-note-preview:free`, OpenRouter) |

## Next steps (TD 2, 18/11/2026)

- Roles rotate. Read `atelier-vote.py` and `enonce-td2-en.md` before the session.
- Write `vote_k_sur_n` in `skeleton-multi-llm-en.py` and run `atelier-vote.py --traces traces-td1.csv` on the twenty questions.
- Wrong consensus: check C10 and C19 with the fixed panel, then explain the cause in the SQL and an independent check that detects it.
- Routing rule: one line per family, justified by the cells above. Then run `atelier-routage.py` before and after adapting it.
- Optional: rerun Qwen on C18 with an allocation agreed with the instructor, in separate experiment files.

No help needed at this stage.
