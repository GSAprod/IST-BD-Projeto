1.
SELECT 
    DISTINCT cust.name
FROM 
    customer AS cust, 
    contains AS cont, 
    order_ AS o, 
    product AS p
WHERE 
    EXTRACT(YEAR FROM o.date)=2023
    AND p.price > 50
    AND p.sku = cont.sku
    AND cont.order_no = o.order_no
    AND o.cust_no = cust.cust_no;

-- em alternativa (qual destas duas opcoes preferem?)

SELECT 
    DISTINCT customer.name
FROM 
    customer JOIN order_ USING (cust_no) JOIN contains USING (order_no) JOIN product USING (sku)
WHERE 
    EXTRACT(YEAR FROM date)=2023
    AND price > 50;

2.
SELECT 
    DISTINCT e.name
FROM 
    employee AS e, customer AS c, order_ AS o, process AS p, works AS w, 
    warehouse AS wh
WHERE 
    EXTRACT(YEAR FROM o.date)=2023
    AND EXTRACT(MONTH FROM o.date)=01
    AND o.order_no = p.order_no
    AND p.ssn = e.ssn
    AND e.ssn = w.ssn
    AND w.address = wh.address
EXCEPT
SELECT 
    DISTINCT e.name
FROM 
    employee AS e, works AS w, office AS of 
WHERE            
    e.ssn = w.ssn
    AND w.address = of.address;


3.
SELECT p.sname
FROM contains AS c, product AS p
WHERE c.qty = (SELECT c2.sku, MAX(c2.qty) AS max_qty
FROM contains AS c2, product AS p
WHERE p.sku = c2. sku
GROUP BY sku);

-- A expressao acima nao me esta a dar resultados certos :/
-- Consegui ter um resultado com esta expressao abaixo:
SELECT name FROM product JOIN contains USING (sku)
GROUP BY sku HAVING SUM(qty) >= ALL (
    SELECT SUM(qty)
    FROM contains 
    GROUP BY sku
);

4.
SELECT o.order_no, SUM(price * qty) AS total_price
FROM contains AS c, product AS p, order_ AS o
WHERE p.sku = c.sku
    AND c.order_no = o.order_no
GROUP BY o.order_no;

-- em alternativa (qual destas duas opcoes preferem?)

SELECT order_no, SUM(price * qty) AS total_price 
FROM order_ JOIN contains USING (order_no) JOIN product USING (sku)
GROUP BY order_no;
