
import sqlite3

# Independent cross-check of role A by role B
conn = sqlite3.connect(
    "file:data/boutique.sqlite?mode=ro",
    uri=True
)

questions = {
    "C01": ("2026-03-01 00:00:00", "2026-06-01 00:00:00"),
    "C04": ("2026-01-01 00:00:00", "2026-10-01 00:00:00"),
    "C05": ("2026-06-01 00:00:00", "2026-06-02 00:00:00"),
    "C06": ("2025-01-01 00:00:00", "2026-01-01 00:00:00")
}

for case_id, (start, end) in questions.items():
    print(f"\n===== {case_id} =====")

    # Method 1: Direct SQL calculation
    query = """
    SELECT COALESCE(SUM(o.quantity_product * p.price), 0)
           AS revenue_cents
    FROM orders AS o
    JOIN product AS p ON o.product_id = p.product_id
    WHERE o.date >= ? AND o.date < ?
    """

    result = conn.execute(query, (start, end)).fetchone()[0]

    # Method 2: Independent check by order
    check_query = """
    SELECT o.order_id,
           SUM(o.quantity_product * p.price)
    FROM orders AS o
    JOIN product AS p ON o.product_id = p.product_id
    WHERE o.date >= ? AND o.date < ?
    GROUP BY o.order_id
    """

    rows = conn.execute(check_query, (start, end)).fetchall()
    verification = sum(amount for order_id, amount in rows)

    print("SQL result:", result)
    print("Verification by order:", verification)
    print("CONSISTENT:", result == verification)

conn.close()
