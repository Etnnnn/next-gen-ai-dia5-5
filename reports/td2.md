# TD 2 report, 18/11/2026

Sub-group DIA5-G5 (Kerry Assohoun, Sam Olivares, Etienne Padelo, Armand Bussolino, Shayan Karimi), instructor Paul Gabriel. Pack `2026-11-18-students-5` (TD 2 statement, final version of 18/11/2026). Input data: TD 1 traces and references, unchanged (`traces-td1.csv`, 103 real attempts; `reference-td1.csv`, 20/20). No new network call was made in this session.

## What we did

| Step | Pair | Completed | Evidence |
|---|---|---|---|
| 1. k-of-n vote, 2-of-3 vs 3-of-5 on the twenty questions | A (Shayan, Etienne) | yes | [`skeleton-multi-llm-en.py`](../skeleton-multi-llm-en.py) (`Orchestrateur.vote_k_sur_n`), [`td2_vote_table.py`](../td2_vote_table.py), [`vote-td2-2of3-vs-3of5.csv`](../vote-td2-2of3-vs-3of5.csv) |
| 2. Wrong consensus | B | yes | [`reports/td2/step2-wrong-consensus-pair-B.md`](td2/step2-wrong-consensus-pair-B.md) |
| 3. Routing rule | C | yes | [`reports/td2/step3-routing-pair-C.md`](td2/step3-routing-pair-C.md), [`atelier-routage.py`](../atelier-routage.py), [`routage-avant.jsonl`](td2/routage-avant.jsonl), [`routage-apres.jsonl`](td2/routage-apres.jsonl) |

## Step 1: the k-of-n vote

### The method

`Orchestrateur.vote_k_sur_n(self, traces_question, k)` follows the five rules of the docstring contract:

1. **Who votes.** Only a proposal with `verdict == "executed"` and a non-`None` value casts a vote. An error (invalid SQL, HTTP 429, missing row) stays in n without a vote, so an unavailable member makes consensus harder, never easier.
2. **k is a strict majority of n.** n is the whole panel, unavailable members included. If `n // 2 < k <= n` does not hold, the method raises `ValueError`. This also covers an empty panel, and it rejects a boolean or non-integer k.
3. **Duplicates.** Two proposals with the same `(provider, model_requested)` raise `ValueError`, even if one of them is an error. A duplicate is not a second vote.
4. **Consensus.** If one value collects at least k votes, the method returns `{"consensus": True, "value": v, "votes": count, "models": [...]}`. The `models` list holds the agreeing members as `provider:model_requested`, in panel order. Because k > n/2, at most one value can reach k, so ties cannot occur.
5. **Abstention.** Otherwise the method returns `{"consensus": False, "value": None, "votes": <largest count>, "models": []}`. It never invents a value. `votes` is 0 when nobody could vote.

The method never sees the reference. `atelier-vote.py` and `td2_vote_table.py` compare the decision with `reference-td1.csv` only after it has been made. `self` is not used, because `atelier-vote.py` calls the method unbound (`self=None`).

### Checks

```powershell
python atelier-vote.py                                     # four synthetic examples (nature: simulation)
python atelier-vote.py --traces traces-td1.csv --case C02  # one real question, fixed panel, k=2
python td2_vote_table.py --check                           # contract checks (11 cases)
python td2_vote_table.py --csv vote-td2-2of3-vs-3of5.csv   # the table below
```

The synthetic examples of `atelier-vote.py` are invented values, not shop data. All four give the expected result:

| Example | Values | Decision | Reference 100 |
|---|---|---|---|
| agreement | 100, 100, 120 | consensus 100 (2 votes) | yes |
| disagreement | 100, 110, 120 | abstain (max 1) | - |
| unavailable | 100, error, error | abstain (max 1): the two errors stay in n=3 | - |
| wrong consensus | 0, 0, 100 | consensus 0 (2 votes) | **no** |

`td2_vote_table.py --check` passes all 11 cases:

- `ValueError` for:
  - k=1 of 3;
  - k=4 of 3;
  - k=2 of 4 (not strict);
  - a duplicate pair;
  - a duplicate pair where one copy is an error;
  - an empty panel.
- Correct returns for:
  - errors kept in n;
  - an executed proposal with a `None` value that does not vote;
  - 3-of-5 with two errors;
  - a 2/2/1 split at k=3 that abstains;
  - the value 0 counted as a real value.

### Building the proposals from the TD 1 traces

For each question we take each model's **last** row in `traces-td1.csv` (chronological export, `nature = real`), using the same rule as `atelier-vote.py`:

- a row with verdict `correct` or `incorrect` and a value becomes an `executed` proposal;
- a row with `sql_invalid` or `not_executed`, or no row at all, becomes an `error` that stays in n.

The vote does not receive the `correct`/`incorrect` label, only the value. Three cells had a retry:

- **qwen C16 and C17**: an HTTP 429 first, then a value on the second attempt. That value is the one that votes.
- **qwen C18**: HTTP 429 twice. It is unavailable and stays in n.

We checked that the `reference` column of the traces is identical to `reference-td1.csv` on all 103 rows.

Panels:

- **2-of-3**: the fixed panel of `atelier-vote.py`, k=2 — `groq:openai/gpt-oss-120b` (120b), `openrouter:cohere/north-mini-code:free` (cohere), `groq:qwen/qwen3.8-27b` (qwen).
- **3-of-5**: the same three models plus `groq:openai/gpt-oss-20b` (20b) and `openrouter:dots-studio/dots-3-note-preview:free` (dots), k=3.

### The twenty decisions

In the ballots column, the first three models form the fixed panel. A value is what the model voted; `sql_invalid` and `not_executed` mean the model stayed in n without a vote.

| Question | Ballots (120b, cohere, qwen \| 20b, dots) | 2-of-3 | = ref | 3-of-5 | = ref | Reference | Changed |
|---|---|---|---|---|---|---|---|
| C01 | 792800, 792800, 792800 \| 792800, 792800 | consensus 792800 (3) | yes | consensus 792800 (5) | yes | 792800 | |
| C02 | 590320, sql_invalid, 590320 \| 0, 135000 | consensus 590320 (2) | yes | abstain (max 2) | - | 590320 | **yes** |
| C03 | 936350 ×3 \| 936350 ×2 | consensus 936350 (3) | yes | consensus 936350 (5) | yes | 936350 | |
| C04 | 2826250 ×3 \| 2826250 ×2 | consensus 2826250 (3) | yes | consensus 2826250 (5) | yes | 2826250 | |
| C05 | 38480 ×3 \| 38480 ×2 | consensus 38480 (3) | yes | consensus 38480 (5) | yes | 38480 | |
| C06 | 0 ×3 \| 0 ×2 | consensus 0 (3) | yes | consensus 0 (5) | yes | 0 | |
| C07 | 13970 ×3 \| 13970 ×2 | consensus 13970 (3) | yes | consensus 13970 (5) | yes | 13970 | |
| C08 | 605580, 0, 605580 \| 605580, 605580 | consensus 605580 (2) | yes | consensus 605580 (4) | yes | 605580 | |
| C09 | 487980, sql_invalid, 0 \| 399610, 47900 | abstain (max 1) | - | abstain (max 1) | - | 487980 | |
| C10 | 558980, 119410, 119410 \| 558980, 119410 | consensus 119410 (2) | **no** | consensus 119410 (3) | **no** | 558980 | |
| C11 | 446690, 0, 446690 \| 322160, 446690 | consensus 446690 (2) | yes | consensus 446690 (3) | yes | 446690 | |
| C12 | 1666490 ×3 \| 1666490 ×2 | consensus 1666490 (3) | yes | consensus 1666490 (5) | yes | 1666490 | |
| C13 | 107740 ×3 \| 107740 ×2 | consensus 107740 (3) | yes | consensus 107740 (5) | yes | 107740 | |
| C14 | 0 ×3 \| 0 ×2 | consensus 0 (3) | yes | consensus 0 (5) | yes | 0 | |
| C15 | 168680, 314020, 0 \| 168680, 168680 | abstain (max 1) | - | consensus 168680 (3) | yes | 168680 | **yes** |
| C16 | 376740, 595500, 367050 \| 376740, 376740 | abstain (max 1) | - | consensus 376740 (3) | yes | 376740 | **yes** |
| C17 | 258180, 371990, 248490 \| 258180, 152730 | abstain (max 1) | - | abstain (max 2) | - | 258180 | |
| C18 | 62480, 62480, not_executed (429 ×2) \| 62480, 39580 | consensus 62480 (2) | yes | consensus 62480 (3) | yes | 62480 | |
| C19 | 1990, 83580, 83580 \| 1990, sql_invalid | consensus 83580 (2) | **no** | abstain (max 2) | - | 1990 | **yes** |
| C20 | 1106090 ×3 \| 1106090 ×2 | consensus 1106090 (3) | yes | consensus 1106090 (5) | yes | 1106090 | |

The same table, generated by the script, is in [`vote-td2-2of3-vs-3of5.csv`](../vote-td2-2of3-vs-3of5.csv).

### Summary

| | Consensus correct | Consensus wrong | Abstention |
|---|---|---|---|
| 2-of-3 (fixed panel) | 14 | 2 (C10, C19) | 4 (C09, C15, C16, C17) |
| 3-of-5 (all five) | 15 | 1 (C10) | 4 (C02, C09, C17, C19) |

For comparison, the best single model in TD 1 (120b) is correct on 20/20 of these cells ([`td1/results/model-question-comparison-en.csv`](../td1/results/model-question-comparison-en.csv)).

The 3-of-5 quorum removes one wrong consensus (C19) and recovers two correct values (C15, C16). In exchange, it loses one correct value (C02) to an abstention.

**Neither vote is ever more accurate than the best single model.** The vote does not create accuracy; it turns some disagreements into abstentions. In these traces, the price of that is losing correct answers that 120b alone had.

### The four questions where the decision changes

- **C02: correct consensus → abstention.**
  - 2-of-3: 120b and qwen both return 590320. Cohere's SQL is invalid (`syntax_error near "AS"`), so cohere stays in n=3 without voting. 2 votes ≥ k=2, so the method keeps 590320, which equals the reference.
  - 3-of-5: 20b returns 0 and dots returns 135000, two different wrong values. Neither adds support to 590320, which still has only 2 votes against k=3.
  - Cohere's invalid SQL still counts in n=5. So the larger panel needs one more agreeing member, and none of the extra members provides it. The quorum abstains on a question the small panel answered correctly.
- **C15: abstention → correct consensus.**
  - 2-of-3: the panel splits three ways (120b 168680, cohere 314020, qwen 0), max 1 vote, so it abstains.
  - 3-of-5: 20b and dots both return 168680, the value 120b already had. That makes 3 votes = k, and 168680 equals the reference.
- **C16: abstention → correct consensus.**
  - 2-of-3: 120b 376740, cohere 595500, qwen 367050 (qwen's second attempt, after an HTTP 429), so it abstains.
  - 3-of-5: 20b and dots join 120b on 376740. That makes 3 votes, equal to the reference.
  - The 429 did not affect the outcome here: if qwen had stayed unavailable, the 2-of-3 panel would still have abstained (1 vote out of 3).
- **C19: wrong consensus → abstention.**
  - 2-of-3: cohere and qwen agree on 83580 against 120b's 1990. That is 2 votes, so the panel **keeps a wrong value** (reference 1990).
  - 3-of-5: 20b returns 1990, so the split is 2-2. Dots stays in n with invalid SQL (`syntax_error near "AS"`). The maximum is 2 < k=3, so it abstains.
  - The larger quorum turns a wrong answer into "no answer". That is the safer failure for a figure shown to a customer or an amount paid out.

### Other cases to note (decision unchanged)

- **C10: the same wrong consensus in both panels.**
  - Cohere, qwen and dots agree on 119410. 120b and 20b agree on 558980, the reference.
  - The wrong value wins 2-of-3 and still wins 3-of-5 (3 against 2).
  - Agreement between independent families is therefore not proof of correctness, as Lecture 2 states. This is the natural candidate for Pair B (Step 2).
- **C18: an unavailable member does not block consensus.** Qwen hit HTTP 429 twice and stays in n without a vote. 120b and cohere still reach 2 of 3, and 3 of 5 with 20b.
- **C08 and C11.** Cohere returns 0 on both, but the panel outvotes it.
- **C09 and C17: abstention in both panels.**
  - C09: four different values and one invalid SQL.
  - C17: 258180 gets only 2 votes (120b, 20b) out of 5.
  - Here a vote alone cannot answer: a reference or a review is needed (input for the Step 3 routing rule).

### Limitations

- The traces hold a single run per model and per question (plus retries after a 429). Model sampling is not deterministic, so another run could change the C02, C15, C16 and C19 decisions, which all hang on one vote.
- The 2-of-3 panel is fixed by `atelier-vote.py`. With 120b, cohere and qwen, it does not contain the best pair available in TD 1, which would be 120b with 20b. However, 120b and 20b both come from OpenAI, so they are not two distinct families.
- In 3-of-5, 120b and 20b are two models from the same family (OpenAI gpt-oss). The 3-of-5 quorum therefore has only four distinct families. On C15 and C16 it is 120b and 20b, with dots, that form the majority.

## Contributions

- Pair A (Step 1): Shayan Karimi, Etienne Padelo: `vote_k_sur_n`, `td2_vote_table.py`, the 2-of-3 vs 3-of-5 table and its analysis.
- Pair B (Step 2): completed. C10 is a wrong consensus: Cohere, Qwen and Dots returned 119410 instead of 558980 cents. Both 2-of-3 and 3-of-5 select the wrong value. Independent SQLite checks found 439570 missing cents across customers C004, C005, C007 and C022. Full SQL analysis: [`reports/td2/step2-wrong-consensus-pair-B.md`](td2/step2-wrong-consensus-pair-B.md).
- Pair C (Step 3): _to fill_.

## Next steps

_To fill after Steps 2 and 3._
