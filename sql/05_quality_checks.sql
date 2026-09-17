USE restaurant_analytics;
-- Expect four counts matching data/raw/manifest.json.
SELECT 'servers' AS table_name,COUNT(*) AS row_count FROM servers
UNION ALL SELECT 'menu_items',COUNT(*) FROM menu_items
UNION ALL SELECT 'orders',COUNT(*) FROM orders
UNION ALL SELECT 'order_items',COUNT(*) FROM order_items;
-- All following issue counts should be zero.
SELECT 'orders_without_lines' AS issue,COUNT(*) AS issue_count
FROM orders o LEFT JOIN order_items i ON i.order_id=o.order_id WHERE i.order_id IS NULL
UNION ALL
SELECT 'orphan_order_lines',COUNT(*) FROM order_items i LEFT JOIN orders o ON o.order_id=i.order_id WHERE o.order_id IS NULL
UNION ALL
SELECT 'orphan_menu_lines',COUNT(*) FROM order_items i LEFT JOIN menu_items m ON m.item_id=i.item_id WHERE m.item_id IS NULL
UNION ALL
SELECT 'cancelled_in_revenue',COUNT(*) FROM v_order_metrics WHERE status<>'completed'
UNION ALL
SELECT 'financial_identity',COUNT(*) FROM v_order_metrics
WHERE gross_sales-discount_amount<>net_sales OR net_sales-ingredient_cost<>contribution_amount;
SELECT (SELECT SUM(net_sales) FROM v_line_metrics)-(SELECT SUM(net_sales) FROM v_order_metrics)
       AS line_order_difference; -- zero
