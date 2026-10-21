"""Références TD 1, membre E : questions C15, C16, C17, C19.

À placer dans le dossier kit-td1 (au même niveau que le dossier data/).
1. Contrôles : produits présents et clients ayant exactement 25 ans au 2026-09-25.
2. Calcul SQL sur data/boutique.sqlite ouverte en lecture seule.
3. Recalcul indépendant en Python sur les fichiers CSV.
4. Comparaison des deux, puis affichage des requêtes à recopier dans reference-td1.csv.

"""
import csv
import sqlite3
from datetime import date
from pathlib import Path

KIT = Path(__file__).resolve().parent
DATA = KIT / "data"
DB = DATA / "boutique.sqlite"

# --- 1. Requêtes SQL de référence -------------------------------------------
# Âge révolu au 2026-09-25 : différence d'années, moins 1 si l'anniversaire
# (mois-jour) n'est pas encore passé à cette date.
AGE25 = ("2026 - CAST(substr(c.birth_date, 1, 4) AS INTEGER) "
         "- ('09-25' < substr(c.birth_date, 6, 5)) = 25")

BASE = ("SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents "
        "FROM orders o "
        "JOIN product p ON p.product_id = o.product_id "
        "JOIN customers c ON c.customer_id = o.customer_id "
        "WHERE ")

QUERIES = {
    "C15": BASE + "o.date >= '2026-03-01 00:00:00' AND o.date < '2026-06-01 00:00:00' AND " + AGE25,
    "C16": BASE + "o.product_id IN ('a', 'b', 'c') AND " + AGE25,
    "C17": BASE + "o.product_id IN ('a', 'b', 'c') "
                  "AND o.date >= '2026-01-01 00:00:00' AND o.date < '2026-07-01 00:00:00' AND " + AGE25,
    "C19": BASE + "o.product_id = 'd' "
                  "AND o.date >= '2026-09-01 00:00:00' AND o.date < '2026-10-01 00:00:00' AND " + AGE25,
}

# --- 2. Recalcul indépendant sur les CSV ------------------------------------
def read_csv(name):
    with open(DATA / name, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

def age(birth, ref):
    return ref.year - birth.year - ((ref.month, ref.day) < (birth.month, birth.day))

def csv_revenue(orders, prices, births, start=None, end=None, products=None,
                ref=date(2026, 9, 25)):
    total = 0
    for o in orders:
        if start and o["date"] < start:
            continue
        if end and o["date"] >= end:
            continue
        if products and o["product_id"] not in products:
            continue
        if age(births[o["customer_id"]], ref) != 25:
            continue
        total += int(o["quantity_product"]) * prices[o["product_id"]]
    return total


def main():
    if not DB.exists():
        raise SystemExit(f"Base introuvable : {DB}\nPlace ce script dans le dossier kit-td1.")

    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    con.execute("PRAGMA query_only = 1")

    print("=== Produits ===")
    for row in con.execute("SELECT product_id, price FROM product ORDER BY product_id"):
        print(f"  {row[0]!r:6} prix = {row[1]} centimes")

    print("\n=== Clients ayant exactement 25 ans au 2026-09-25 ===")
    print("  (attendu : nés entre 2000-09-26 et 2001-09-25 inclus)")
    eligible = con.execute(
        "SELECT c.customer_id, c.birth_date FROM customers c WHERE " + AGE25 +
        " ORDER BY c.birth_date").fetchall()
    for cid, birth in eligible:
        print(f"  {cid}  né(e) le {birth}")
    print(f"  -> {len(eligible)} client(s)")

    print("\n=== Clients nés près des bornes (contrôle visuel) ===")
    for cid, birth in con.execute(
            "SELECT customer_id, birth_date FROM customers "
            "WHERE substr(birth_date, 6, 5) BETWEEN '09-23' AND '09-27' "
            "AND substr(birth_date, 1, 4) IN ('2000', '2001') ORDER BY birth_date"):
        print(f"  {cid}  né(e) le {birth}  -> âge au 2026-09-25 : "
              f"{age(date.fromisoformat(birth), date(2026, 9, 25))}")

    sql_values = {}
    for qid, sql in QUERIES.items():
        rows = con.execute(sql).fetchall()
        assert len(rows) == 1 and len(rows[0]) == 1, f"{qid} : doit renvoyer 1 ligne, 1 colonne"
        sql_values[qid] = rows[0][0]
    con.close()

    prices = {r["product_id"]: int(r["price"]) for r in read_csv("product.csv")}
    births = {r["customer_id"]: date.fromisoformat(r["birth_date"]) for r in read_csv("customers.csv")}
    orders = read_csv("orders.csv")
    csv_values = {
        "C15": csv_revenue(orders, prices, births, "2026-03-01 00:00:00", "2026-06-01 00:00:00"),
        "C16": csv_revenue(orders, prices, births, products={"a", "b", "c"}),
        "C17": csv_revenue(orders, prices, births, "2026-01-01 00:00:00", "2026-07-01 00:00:00", {"a", "b", "c"}),
        "C19": csv_revenue(orders, prices, births, "2026-09-01 00:00:00", "2026-10-01 00:00:00", {"d"}),
    }

    print("\n=== Comparaison SQL / CSV ===")
    all_ok = True
    for qid in QUERIES:
        ok = sql_values[qid] == csv_values[qid]
        all_ok &= ok
        print(f"  {qid}  SQL = {sql_values[qid]:>10}   CSV = {csv_values[qid]:>10}   "
              f"{'OK' if ok else 'DIFFÉRENT -> à investiguer'}")

    print("\n=== À recopier dans reference-td1.csv (requête sur une ligne + valeur) ===")
    for qid, sql in QUERIES.items():
        print(f"\n{qid}\n  requête : {sql};\n  valeur  : {sql_values[qid]}")

    print("\n" + ("Tout concorde. Faire vérifier par un autre membre, puis montrer à l'enseignant."
                  if all_ok else "ATTENTION : au moins une différence, ne rien enregistrer avant d'avoir compris."))
    
     # --- 5. Écriture de reference_E.csv (case_id, sql, revenue_cents) --------
    if all_ok:
        out = KIT / "reference_E.csv"
        with open(out, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["case_id", "sql", "revenue_cents"])
            for qid, sql in QUERIES.items():
                writer.writerow([qid, sql + ";", sql_values[qid]])
        print(f"\nFichier écrit : {out}")
    else:
        print("\nreference_E.csv NON écrit tant que SQL et CSV ne concordent pas.")

if __name__ == "__main__":
    main()
