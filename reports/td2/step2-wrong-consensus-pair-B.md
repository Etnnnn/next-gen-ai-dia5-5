# Step 2 – Wrong Consensus Analysis (Pair B)

## Case selection

We analyzed the 103 rows in `traces-td1.csv` and found two cases where at least two different models returned the same incorrect value:

| Case | Wrong value | Reference | Models |
|---|---:|---:|---|
| C10 | 119410 | 558980 | Cohere, Qwen, Dots |
| C19 | 83580 | 1990 | Cohere, Qwen |

We selected C10 for detailed analysis.

C10 asks for the revenue, in euro cents, of orders placed when customers were exactly 25 years old.

## Model results

| Model | Value | Verdict |
|---|---:|---|
| GPT-OSS 120B | 558980 | Correct |
| GPT-OSS 20B | 558980 | Correct |
| Cohere North Mini Code | 119410 | Incorrect |
| Qwen 3.8 27B | 119410 | Incorrect |
| Dots 3 Note Preview | 119410 | Incorrect |

## Voting results

The fixed panel in `atelier-vote.py` contains GPT-OSS 120B, Cohere and Qwen.

- Fixed 2-of-3: 119410 wins with 2 votes (Cohere and Qwen).
- Full 3-of-5: 119410 wins with 3 votes (Cohere, Qwen and Dots).
- Correct reference: 558980.

Both voting rules produce a wrong consensus.

These results were calculated from the stored traces. The official vote function was not yet implemented when we tested it.

## SQL error analysis

### Qwen

```sql
SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN product p ON o.product_id = p.product_id
WHERE (
    (strftime('%Y', o.date) - strftime('%Y', c.birth_date)) = 25
    AND (strftime('%m', o.date) || strftime('%d', o.date)) >=
        (strftime('%m', c.birth_date) || strftime('%d', c.birth_date))
)
OR (
    (strftime('%Y', o.date) - strftime('%Y', c.birth_date)) = 24
    AND (strftime('%m', o.date) || strftime('%d', o.date)) <
        (strftime('%m', c.birth_date) || strftime('%d', c.birth_date))
);
```

Qwen handles the age calculation incorrectly. The second condition uses a year difference of 24 instead of handling customers with a year difference of 26 whose birthday has not yet occurred.

As a result, Qwen misses four customers who were exactly 25 at the time of their orders.

### Dots

```sql
SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN product p ON o.product_id = p.product_id
WHERE (
    CAST(substr(o.date, 1, 4) AS INTEGER)
    - CAST(substr(c.birth_date, 1, 4) AS INTEGER) = 25
    AND (
        CAST(substr(o.date, 6, 2) AS INTEGER) >
        CAST(substr(c.birth_date, 6, 2) AS INTEGER)
        OR (
            CAST(substr(o.date, 6, 2) AS INTEGER) =
            CAST(substr(c.birth_date, 6, 2) AS INTEGER)
            AND CAST(substr(o.date, 9, 2) AS INTEGER) >=
                CAST(substr(c.birth_date, 9, 2) AS INTEGER)
        )
    )
);
```

Dots only accepts a year difference of 25. This excludes customers born in 2000 who were still 25 when they placed orders in 2026.

Both queries use the correct joins, but their `WHERE` conditions are incorrect.

## Independent SQLite verification

We executed a diagnostic query directly on `data/boutique.sqlite` using the correct age interval:

```sql
SELECT
    o.customer_id,
    SUM(o.quantity_product * p.price) AS revenue_cents
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN product p ON o.product_id = p.product_id
WHERE date(o.date) >= date(c.birth_date, '+25 years')
  AND date(o.date) < date(c.birth_date, '+26 years')
GROUP BY o.customer_id
ORDER BY o.customer_id;
```

Results:

| Customer ID | Correct revenue | Qwen / Dots revenue | Missing revenue |
|---|---:|---:|---:|
| C004 | 150260 | 0 | 150260 |
| C005 | 150240 | 0 | 150240 |
| C007 | 118740 | 0 | 118740 |
| C008 | 86860 | 86860 | 0 |
| C009 | 32550 | 32550 | 0 |
| C022 | 20330 | 0 | 20330 |
| **Total** | **558980** | **119410** | **439570** |

The independent SQL calculation confirms the reference value of 558980 cents.

Qwen and Dots both miss customers C004, C005, C007 and C022, accounting for 439570 missing cents.

## Conclusion

Three different models produced the same wrong answer for C10.

The fixed 2-of-3 panel and the full 3-of-5 quorum both select this incorrect answer.

This example shows that agreement between AI models does not guarantee correctness. Independent SQL verification is necessary.

## Trace verification

The TD1 CSV contains 103 rows but 100 unique model-question cells.

Three cells (Qwen C16, C17 and C18) contain two attempts each. We keep the latest attempt for each cell.

C16 and C17 have an incorrect executed result on the second attempt. C18 remains not executed.

These duplicates do not affect the C10 analysis.
