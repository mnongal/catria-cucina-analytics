USE restaurant_analytics;
-- Grain: one item line on a completed check. Round discount per line, then subtract.
-- Historical snapshots on order_items protect revenue from menu price changes.
CREATE OR REPLACE VIEW v_line_metrics AS
SELECT b.*, b.gross_sales-b.discount_amount AS net_sales,
       b.gross_sales-b.discount_amount-b.ingredient_cost AS contribution_amount
FROM (
  SELECT oi.order_item_id,oi.order_id,oi.item_id,m.item_name,m.category,oi.quantity,
         o.order_date,oi.quantity*oi.unit_price AS gross_sales,
         ROUND(oi.quantity*oi.unit_price*o.discount_percent/100,2) AS discount_amount,
         oi.quantity*oi.unit_cost AS ingredient_cost
  FROM order_items oi
  JOIN orders o ON o.order_id=oi.order_id
  JOIN menu_items m ON m.item_id=oi.item_id
  WHERE o.status='completed'
) b;

-- Aggregate BEFORE joining order attributes. One row per completed order.
CREATE OR REPLACE VIEW v_order_metrics AS
SELECT o.*,s.server_name,t.gross_sales,t.discount_amount,t.net_sales,
       t.ingredient_cost,t.contribution_amount,t.units
FROM orders o
JOIN (
  SELECT order_id,SUM(gross_sales) AS gross_sales,SUM(discount_amount) AS discount_amount,
         SUM(net_sales) AS net_sales,SUM(ingredient_cost) AS ingredient_cost,
         SUM(contribution_amount) AS contribution_amount,SUM(quantity) AS units
  FROM v_line_metrics GROUP BY order_id
) t ON t.order_id=o.order_id
JOIN servers s ON s.server_id=o.server_id;
