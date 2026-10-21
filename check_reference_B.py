import sqlite3

# Open the database in read-only mode
conn = sqlite3.connect(
    "file:data/boutique.sqlite?mode=ro",
    uri=True
)

# Questions assigned to role B
questions = {
    "C07": {
        "start": "2026-05-31 00:00:00",
        "end": "2026-06-01 00:00:00"
    },
    "C20": {
        "start": "2026-06-01 00:00:00",
        "end": "2026-09-01 00:00:00"
    }
}

for case_id, dates in questions.items():

    print(f"\n===== {case_id} =====")

    # Method 1: Direct revenue calculation
    query = """
    SELECT SUM(o.quantity_product * p.price) AS revenue_cents
    FROM orders AS o
    JOIN product AS p ON o.product_id = p.product_id
    WHERE o.date >= ?
      AND o.date < ?;
    """

    result = conn.execute(
        query, (dates["start"], dates["end"])
    ).fetchone()[0]

    # Method 2: Independent verification by product
    verification_query = """
    SELECT
        o.product_id,
        SUM(o.quantity_product) AS quantity,
        p.price
    FROM orders AS o
    JOIN product AS p ON o.product_id = p.product_id
    WHERE o.date >= ?
      AND o.date < ?
    GROUP BY o.product_id, p.price;
    """

    rows = conn.execute(
        verification_query, (dates["start"], dates["end"])
    ).fetchall()

    verification = sum(
        quantity * price
        for product, quantity, price in rows
    )

    print("SQL result:", result)
    print("Independent verification:", verification)
    print("VERIFIED:", result == verification)

# ==========================================
# C12 and C13 - Product revenue
# ==========================================

product_questions = {
    "C12": {
        "products": ["a", "b", "c"],
        "start": None,
        "end": None
    },
    "C13": {
        "products": ["a", "c"],
        "start": "2026-04-01 00:00:00",
        "end": "2026-05-01 00:00:00"
    }
}

for case_id, params in product_questions.items():

    print(f"\n===== {case_id} =====")

    placeholders = ",".join("?" for _ in params["products"])

    conditions = [f"o.product_id IN ({placeholders})"]
    values = list(params["products"])

    if params["start"] is not None:
        conditions.append("o.date >= ?")
        conditions.append("o.date < ?")
        values.extend([params["start"], params["end"]])

    where_clause = " AND ".join(conditions)

    # Method 1: Direct SQL calculation
    query = f"""
    SELECT COALESCE(SUM(o.quantity_product * p.price), 0)
           AS revenue_cents
    FROM orders AS o
    JOIN product AS p ON o.product_id = p.product_id
    WHERE {where_clause};
    """

    result = conn.execute(query, values).fetchone()[0]

    # Method 2: Grouped calculation
    verification_query = f"""
    SELECT o.product_id, SUM(o.quantity_product), p.price
    FROM orders AS o
    JOIN product AS p ON o.product_id = p.product_id
    WHERE {where_clause}
    GROUP BY o.product_id, p.price;
    """

    rows = conn.execute(verification_query, values).fetchall()

    verification = sum(
        quantity * price
        for product, quantity, price in rows
    )

    print("SQL result:", result)
    print("Independent verification:", verification)
    print("VERIFIED:", result == verification)
    
conn.close()