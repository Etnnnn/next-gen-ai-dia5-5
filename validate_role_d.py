#!/usr/bin/env python3
"""Offline role D references: sandboxed SQLite versus a separate CSV computation."""
import csv
import hashlib
import importlib.util
import json
import platform
import sqlite3
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import sandbox_sqlite

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'evidence' / 'role-D'
ASSIGNED = {3, 10, 14, 18}
PEER_C = {2, 8, 9, 11}

# SQL predicates transcribed from C01-C20, independent of the CSV predicates below.
PERIODS = {
    1: ('2026-03-01', '2026-06-01'), 3: ('2026-01-01', '2026-07-01'),
    4: ('2026-01-01', '2026-10-01'), 5: ('2026-06-01', '2026-06-02'),
    6: ('2025-01-01', '2026-01-01'), 7: ('2026-05-31', '2026-06-01'),
    13: ('2026-04-01', '2026-05-01'), 14: ('2026-10-01', '2026-12-01'),
    15: ('2026-03-01', '2026-06-01'), 17: ('2026-01-01', '2026-07-01'),
    18: ('2026-05-01', '2026-06-01'), 19: ('2026-09-01', '2026-10-01'),
    20: ('2026-06-01', '2026-09-01'),
}
AGE_DAYS = {2: '2026-09-25', 8: '2026-09-24', 9: '2026-09-26',
            11: '2026-12-01', 15: '2026-09-25', 16: '2026-09-25',
            17: '2026-09-25', 19: '2026-09-25'}
PRODUCTS = {3: 'abc', 12: 'abc', 13: 'ac', 14: 'abc', 16: 'abc', 17: 'abc', 19: 'd'}


def sql_for(n):
    clauses = []
    if n in PERIODS:
        start, end = PERIODS[n]
        clauses += [f"o.date >= '{start} 00:00:00'", f"o.date < '{end} 00:00:00'"]
    if n in PRODUCTS:
        values = ', '.join(repr(p) for p in PRODUCTS[n])
        clauses.append(f'o.product_id IN ({values})')
    if n in AGE_DAYS or n in (10, 18):
        day = 'date(o.date)' if n in (10, 18) else repr(AGE_DAYS[n])
        clauses.append(f"(CAST(strftime('%Y', {day}) AS INTEGER) - CAST(strftime('%Y', c.birth_date) AS INTEGER) - (strftime('%m-%d', {day}) < strftime('%m-%d', c.birth_date))) = 25")
    sql = ('SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents '
           'FROM orders o JOIN product p ON p.product_id = o.product_id '
           'JOIN customers c ON c.customer_id = o.customer_id')
    return sql + (' WHERE ' + ' AND '.join(clauses) if clauses else '') + ';'


def csv_matches(n, timestamp, birth, product):
    # Different age algorithm: birthday anniversaries rather than year subtraction.
    def age25(day):
        return birth.replace(year=birth.year + 25) <= day < birth.replace(year=birth.year + 26)

    def period(start, end):
        return datetime.fromisoformat(start) <= timestamp < datetime.fromisoformat(end)

    ref25 = age25(date(2026, 9, 25))
    if n == 1: return period('2026-03-01', '2026-06-01')
    if n == 2: return ref25
    if n == 3: return product in {'a', 'b', 'c'} and period('2026-01-01', '2026-07-01')
    if n == 4: return period('2026-01-01', '2026-10-01')
    if n == 5: return period('2026-06-01', '2026-06-02')
    if n == 6: return period('2025-01-01', '2026-01-01')
    if n == 7: return period('2026-05-31', '2026-06-01')
    if n == 8: return age25(date(2026, 9, 24))
    if n == 9: return age25(date(2026, 9, 26))
    if n == 10: return age25(timestamp.date())
    if n == 11: return age25(date(2026, 12, 1))
    if n == 12: return product in {'a', 'b', 'c'}
    if n == 13: return product in {'a', 'c'} and period('2026-04-01', '2026-05-01')
    if n == 14: return product in {'a', 'b', 'c'} and period('2026-10-01', '2026-12-01')
    if n == 15: return ref25 and period('2026-03-01', '2026-06-01')
    if n == 16: return ref25 and product in {'a', 'b', 'c'}
    if n == 17: return ref25 and product in {'a', 'b', 'c'} and period('2026-01-01', '2026-07-01')
    if n == 18: return age25(timestamp.date()) and period('2026-05-01', '2026-06-01')
    if n == 19: return ref25 and product == 'd' and period('2026-09-01', '2026-10-01')
    if n == 20: return period('2026-06-01', '2026-09-01')
    raise ValueError(n)


def read_csv(name):
    with (ROOT / 'data' / (name + '.csv')).open(newline='', encoding='utf-8') as stream:
        return list(csv.DictReader(stream))


def save_json(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    check = subprocess.run([sys.executable, str(ROOT / 'verify-data.py')], capture_output=True, text=True, check=True)
    integrity = json.loads(check.stdout)
    save_json('data-check-before.json', integrity)
    db = ROOT / 'data' / 'boutique.sqlite'
    tables = {name: read_csv(name) for name in ('product', 'customers', 'orders')}
    # Compare all CSV rows with all database rows, not just totals.
    with sqlite3.connect(db.as_uri() + '?mode=ro', uri=True) as con:
        for name, rows in tables.items():
            columns = list(rows[0])
            actual = sorted(tuple(map(str, r)) for r in con.execute('SELECT ' + ','.join(columns) + ' FROM ' + name))
            expected = sorted(tuple(r[c] for c in columns) for r in rows)
            assert actual == expected, name
        counts = {name: con.execute('SELECT COUNT(*) FROM ' + name).fetchone()[0] for name in tables}
        counts['distinct_orders'] = con.execute('SELECT COUNT(DISTINCT order_id) FROM orders').fetchone()[0]
    manifest = json.loads((ROOT / 'data' / 'manifest.json').read_text())
    assert counts == manifest['counts']
    products = {r['product_id']: int(r['price']) for r in tables['product']}
    customers = {r['customer_id']: date.fromisoformat(r['birth_date']) for r in tables['customers']}
    assert all((b.month, b.day) != (2, 29) for b in customers.values())
    refs, checks = [], []
    for n in sorted(ASSIGNED | PEER_C):
        query = sql_for(n)
        result = sandbox_sqlite.execute_query(db, query)
        assert result['ok'] and result['shape_ok'] and result['columns'] == ['revenue_cents'], result
        assert type(result['value']) is int
        selected = [r for r in tables['orders'] if csv_matches(n, datetime.fromisoformat(r['date']), customers[r['customer_id']], r['product_id'])]
        independent = sum(int(r['quantity_product']) * products[r['product_id']] for r in selected)
        assert result['value'] == independent, (n, result, independent)
        refs.append({'case_id': f'C{n:02}', 'sql': query, 'revenue_cents': independent})
        checks.append({'case_id': f'C{n:02}', 'sql_cents': result['value'], 'csv_cents': independent, 'matching_lines': len(selected), 'ok': True})
    # Preserve any peer-filled consolidated references; require exact agreement.
    with (ROOT / 'reference-td1.csv').open(newline='', encoding='utf-8') as stream:
        for row in csv.DictReader(stream):
            if row['revenue_cents'].strip():
                matching = [r for r in refs if r['case_id'] == row['case_id']]
                if matching:
                    assert int(row['revenue_cents']) == matching[0]['revenue_cents'], row
    with (ROOT / 'reference-D.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=['case_id', 'sql', 'revenue_cents'], lineterminator='\n')
        writer.writeheader()
        writer.writerows(r for r in refs if int(r['case_id'][1:]) in ASSIGNED)
    with (ROOT / 'cross-check-C-by-D.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=['case_id', 'sql', 'revenue_cents'], lineterminator='\n')
        writer.writeheader()
        writer.writerows(r for r in refs if int(r['case_id'][1:]) in PEER_C)
    tests = sandbox_sqlite.self_tests(db)
    assert all(t['pass'] for t in tests), tests
    save_json('sandbox-self-tests.json', {'tests': tests, 'all_pass': True})
    save_json('reference-validation.json', {'date_utc': datetime.now(timezone.utc).isoformat(), 'python': platform.python_version(), 'sqlite': sqlite3.sqlite_version, 'counts': counts, 'csv_database_rows_identical': True, 'assigned_D': ['C03', 'C10', 'C14', 'C18'], 'independent_check_of_C': ['C02', 'C08', 'C09', 'C11'], 'checks': checks, 'technical_check_passed': True, 'human_cross_check': 'pending comparison with C actual queries and C review of D', 'instructor_answer_key_check': 'pending'})
    after = json.loads(subprocess.run([sys.executable, str(ROOT / 'verify-data.py')], capture_output=True, text=True, check=True).stdout)
    assert integrity == after
    save_json('data-check-after.json', after)
    print(json.dumps(checks, indent=2))


if __name__ == '__main__':
    main()
