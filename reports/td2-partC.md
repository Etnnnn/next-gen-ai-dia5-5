# TD 2, Step 3 (Pair C): the routing rule

Section to be merged into `reports/td2.md`. Sources: [`model-question-comparison-en.csv`](../model-question-comparison-en.csv) (status of every TD 1 cell), [`questions-td1.json`](../questions-td1.json) (family of every question), [`five-model-summary-en.csv`](../five-model-summary-en.csv) and [`portefeuille-modeles-2026-09-28.csv`](../portefeuille-modeles-2026-09-28.csv) (prices, routes). No new network call.

## 1. Exact TD 1 rates per family

Families come from the `type` field of `questions-td1.json`. A cell counts as correct only with verdict `correct`; `incorrect`, `sql_invalid` and `not_executed` (HTTP 429) are all "not correct", but a 429 is an access failure, not a wrong answer.

| Family | Cells | gpt-oss-120b | gpt-oss-20b | qwen3.8-27b | north-mini-code:free | dots-3-note:free |
|---|---|---|---|---|---|---|
| F1 period | C01 C04 C05 C06 C07 C20 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 |
| F2 age on a reference date | C02 C08 C09 C11 | **4/4** | 1/4 (C02, C09, C11) | 3/4 (C09) | 0/4 (C02, C09 sql_invalid; C08, C11) | 2/4 (C02, C09) |
| F2b age at the order | C10 | **1/1** | 1/1 | 0/1 | 0/1 | 0/1 |
| F3 product list | C03 C12 C13 C14 | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 |
| F1+F2 | C15 | **1/1** | 1/1 | 0/1 | 0/1 | 1/1 |
| F2+F3 | C16 | **1/1** | 1/1 | 0/1 | 0/1 | 1/1 |
| F1+F2+F3 | C17 C19 | **2/2** | 2/2 | 0/2 | 0/2 | 0/2 (C19 sql_invalid) |
| F1+F2b | C18 | **1/1** | 1/1 | 0/1 (429, not executed) | 1/1 | 0/1 |
| **Total** | 20 | 20/20 | 17/20 | 13/20 (+1 not executed) | 11/20 | 15/20 |

**Eligibility choice (stricter than the raw table).** A combined family has 1 or 2 cells, so 1/1 is weak evidence. A model is eligible for a combination only if it is 100 % on the combination **and** on each component family. So gpt-oss-20b (1/4 on F2) and Dots (2/4 on F2) are *not* eligible on F1+F2 or F2+F3, even though they got C15/C16 right. Result:

| Family | Eligible models (TD 1) |
|---|---|
| F1, F3 | all five |
| F2, F1+F2, F2+F3, F1+F2+F3 | gpt-oss-120b only |
| F2b, F1+F2b | gpt-oss-120b, gpt-oss-20b (one cell each: C10, C18) |

**Two wrong consensuses on age families (useful for Pair B and for the checking):**
- C10 (F2b): north-mini-code, qwen and dots all return **119410** (reference 558980). That is 3 identical wrong votes out of 5, so the **3-of-5 quorum validates the wrong value**.
- C19 (F1+F2+F3): north-mini-code and qwen both return **83580** (reference 1990). In the fixed panel (120b, north-mini-code, qwen), the **2-of-3 quorum validates the wrong value**.

So on age families a quorum of these models is *not* a valid check. Their errors are correlated (the same off-by-one-year age logic).

## 2. The rule (one page)

Cost per request on a paid route, with the mean TD 1 token envelope: gpt-oss-20b ≈ 0.000033 USD (641 × 0.018 + 243 × 0.09 per M), gpt-oss-120b ≈ 0.000237 USD (641 × 0.15 + 234 × 0.60 per M), qwen ≈ 0.000206 USD. All five TD 1 routes were free (Groq free plan, OpenRouter `:free`). Among free routes, ties are broken by the cheapest paid fallback of the same model. North-mini-code and Dots have no paid route and are not in the portfolio (Dots is a preview that can be withdrawn).

| Family | First model (cheapest eligible) | Internal dashboard | Figure shown to a customer | Amount paid out | If first model unavailable |
|---|---|---|---|---|---|
| F1 period | gpt-oss-20b (Groq free), 6/6 | none (20b 6/6) | 2-of-3 quorum 20b / 120b / qwen (all 6/6) | 3-of-5 quorum + reference query | next free model (120b, qwen, …): 5 models are 6/6 |
| F3 product list | gpt-oss-20b (Groq free), 4/4 | none (20b 4/4) | 2-of-3 quorum 20b / 120b / qwen (all 4/4) | 3-of-5 quorum + reference query | next free model: 5 models are 4/4 |
| F2 age on a date | gpt-oss-120b (Groq free), 4/4, only eligible model | none (120b 4/4) | deterministic check against the reference template (`refs/C11.sql`: `birth_date <= date(D,'-25 years') AND > date(D,'-26 years')`) | reference query + human review | defer to the Groq refill if the request can wait, else paid OpenRouter route of gpt-oss-120b, else **abstain** |
| F2b age at the order | gpt-oss-120b, 1/1 | none (120b 1/1) | deterministic check (reference age-at-order formula, C10) | reference query + human review | gpt-oss-20b (1/1) or its paid route, else defer, else abstain |
| F1+F2, F2+F3, F1+F2+F3 | gpt-oss-120b, 1/1, 1/1, 2/2 | none | deterministic check | reference query + human review | defer, else paid 120b, else abstain. **No quorum**: C19 shows a wrong 2-of-3 consensus |
| F1+F2b | gpt-oss-120b, 1/1 | none | deterministic check | reference query + human review | gpt-oss-20b (1/1), then defer, paid route, abstain |

Why F2b goes to 120b first, not 20b: 20b is 1/1 on C10, but it failed 3/4 of the closely related F2 questions, and a single cell does not justify the cheaper model.

Consistency with the constraint: `none` is used only for the internal dashboard and only with a model that is 100 % on the family in TD 1. Every customer-facing or paid-out figure goes through a quorum (F1, F3, where all models are 100 %) or a deterministic check (age families, where a quorum is proven unsafe by C10 and C19).

**Limits.** Twenty questions, one run per cell: these are batch-specific hypotheses, not general error rates or a permanent ranking. The paid OpenRouter route of a model is assumed to behave like the Groq free route of the same model (same weights). That assumption is **not measured**. A model chosen with `none` can still be wrong outside these twenty questions.

## 3. Simulator before and after adaptation

- Before: original file kept as [`td2-evidence/atelier-routage-original.py`](td2-evidence/atelier-routage-original.py), output in [`td2-evidence/routage-avant.jsonl`](td2-evidence/routage-avant.jsonl) (7 scenarios, 3 fictitious resources).
- After: [`atelier-routage.py`](../atelier-routage.py) adapted, output in [`td2-evidence/routage-apres.jsonl`](td2-evidence/routage-apres.jsonl).

What changed: `RESOURCES` holds the five TD 1 free routes plus the paid OpenRouter routes of gpt-oss-20b and gpt-oss-120b. The single `level` was replaced by the list of families where the model is eligible (computed from the TD 1 table). `request` now carries `family` and `use` (dashboard / customer / payout). `checks` follows the rule above. Every `reason` cites the TD 1 rate and cells. **The priority order of `choose` is unchanged.**

| Scenario | Request | Before | After |
|---|---|---|---|
| simple | F1, dashboard | run small-free | run groq gpt-oss-20b, check none (20b 6/6 on F1: C01…C20) |
| complex | F2, dashboard | run senior-subscription | run groq gpt-oss-120b (4/4 on F2: C02, C08, C09, C11) |
| deferrable | F2, Groq in 429, refill in 60 min ≤ 120 | defer senior-subscription | defer groq gpt-oss-120b, wake in 60 min |
| urgent | F2, cannot wait, deadline 5 min | run senior-api, 0.30 | run openrouter gpt-oss-120b, 0.000237 USD |
| budget exhausted | F2, budget 0, cannot wait | abstain | abstain (no F2-eligible model available within budget) |
| high impact | F1+F2+F3, payout | run senior-subscription, human review | run groq gpt-oss-120b, reference query + human review |
| unknown capability | F4 (not measured) | abstain | abstain (no TD 1 cell) |
| customer period *(new)* | F1, customer | – | run groq gpt-oss-20b + 2-of-3 quorum 20b/120b/qwen |
| combined age at order, Groq down *(new)* | F1+F2b, customer, cannot wait | – | run openrouter gpt-oss-20b, 0.000033 USD, deterministic check |

Run it with:

```
python3 atelier-routage.py
python3 atelier-routage.py --scenario deferrable
```

## 4. Priority order in the supplied `choose`

`choose` tests three branches in order: (1) `included`: eligible, available, `cash == 0`; (2) `waiting`: eligible, unavailable, `cash == 0`, refill before `deadline_minutes`, and only if `can_wait`; (3) `paid`: available with `cash <= budget`; otherwise `abstain`.

An available subscription (`cash == 0`, `allocation > 0`) falls into branch 1, so it is returned **before** branch 2 is ever evaluated. An exhausted free resource that refills before the deadline is therefore never chosen while included capacity exists. Inside branch 1, `min` on `allocation` prefers a free resource (`allocation 0`) over the subscription (`0.04`) only when both are available.

Why this order makes sense:
- Both cost 0 cash for this request. The subscription is already paid, and an unused allocation is lost at the end of the period.
- Running now gives the answer immediately. `defer` adds latency and risk: reaching the reset time does not prove that capacity is back (the docstring says to measure availability again at wake-up). A 429 can happen again, as for qwen on C18 in TD 1, which failed at the first attempt and at the retry.
- Fewer requests left pending means a simpler service.

When to reverse it (defer to the free route rather than consume the subscription):
- the subscription allocation is **scarce and shared**, and must be kept for urgent or high-impact requests later in the period (for example payouts at month end), while this request has a comfortable deadline;
- the free resource is **more reliable on this family** than the subscription model (higher TD 1 rate), so waiting buys quality, not only money;
- the subscription is billed per use beyond a threshold (`allocation` close to exhaustion), so its real marginal cost is no longer 0.

Operationally: reverse the priority when the request can wait, the refill is well before the deadline, and the remaining subscription allocation is below a reserve kept for non-deferrable requests.
