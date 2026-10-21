-- C09: revenue of customers exactly 25 years old (completed age) on 2026-09-26, all their orders.
-- Exactly 25 on D  <=>  date(D, '-26 years') < birth_date <= date(D, '-25 years')
--                  <=>  '2000-09-26' < birth_date <= '2001-09-26'
SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents
FROM orders o
JOIN product p ON p.product_id = o.product_id
JOIN customers c ON c.customer_id = o.customer_id
WHERE c.birth_date <= date('2026-09-26', '-25 years')
  AND c.birth_date > date('2026-09-26', '-26 years');
