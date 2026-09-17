USE restaurant_analytics;
-- Q01: What are the headline economics? Contribution is before operating expenses.
SELECT COUNT(*) AS completed_orders, SUM(gross_sales) AS gross_sales,
       SUM(discount_amount) AS discount_amount, SUM(net_sales) AS net_sales,
       SUM(ingredient_cost) AS ingredient_cost, SUM(contribution_amount) AS contribution_amount,
       SUM(net_sales)/NULLIF(COUNT(*),0) AS aov,
       100*SUM(contribution_amount)/NULLIF(SUM(net_sales),0) AS contribution_margin_pct
FROM v_order_metrics;

-- Q02: How do sales change by month? Normalize for different calendar lengths.
WITH monthly AS (
 SELECT DATE_FORMAT(order_date,'%Y-%m') AS month,COUNT(*) AS orders,
        SUM(net_sales) AS net_sales,SUM(contribution_amount) AS contribution_amount,
        DAY(LAST_DAY(MIN(order_date))) AS calendar_days
 FROM v_order_metrics GROUP BY DATE_FORMAT(order_date,'%Y-%m')
)
SELECT *,net_sales/orders AS aov,net_sales/calendar_days AS net_sales_per_day,
       100*(net_sales/NULLIF(LAG(net_sales) OVER (ORDER BY month),0)-1) AS mom_net_sales_pct
FROM monthly ORDER BY month;

-- Q03: Which items drive net sales and ingredient contribution?
SELECT item_id,item_name,category,SUM(quantity) AS units,SUM(net_sales) AS net_sales,
       SUM(contribution_amount) AS contribution_amount,
       SUM(contribution_amount)/SUM(quantity) AS contribution_per_unit,
       100*SUM(contribution_amount)/NULLIF(SUM(net_sales),0) AS contribution_margin_pct
FROM v_line_metrics GROUP BY item_id,item_name,category
ORDER BY net_sales DESC,item_id;

-- Q04: Which categories have the highest weighted margin?
SELECT category,SUM(quantity) AS units,SUM(net_sales) AS net_sales,
       SUM(contribution_amount) AS contribution_amount,
       100*SUM(contribution_amount)/NULLIF(SUM(net_sales),0) AS contribution_margin_pct
FROM v_line_metrics GROUP BY category ORDER BY category;

-- Q05: Which weekdays need the most service capacity? Calendar includes zero-order days.
WITH RECURSIVE calendar AS (
 SELECT DATE('2026-01-01') AS d UNION ALL
 SELECT d+INTERVAL 1 DAY FROM calendar WHERE d<'2026-06-30'
), days AS (SELECT WEEKDAY(d) AS weekday,COUNT(*) AS operating_days FROM calendar GROUP BY WEEKDAY(d))
SELECT days.weekday,days.operating_days,COUNT(o.order_id) AS orders,
       COUNT(o.order_id)/days.operating_days AS orders_per_day,
       SUM(o.net_sales) AS net_sales,AVG(o.service_minutes) AS avg_service_minutes
FROM days LEFT JOIN v_order_metrics o ON WEEKDAY(o.order_date)=days.weekday
GROUP BY days.weekday,days.operating_days ORDER BY days.weekday;

-- Q06: When is demand concentrated and service slower? Completed checks only.
WITH RECURSIVE calendar AS (
 SELECT DATE('2026-01-01') AS d UNION ALL
 SELECT d+INTERVAL 1 DAY FROM calendar WHERE d<'2026-06-30'
), days AS (SELECT WEEKDAY(d) AS weekday,COUNT(*) AS operating_days FROM calendar GROUP BY WEEKDAY(d))
SELECT WEEKDAY(o.order_date) AS weekday,HOUR(o.order_time) AS hour,COUNT(*) AS orders,
       COUNT(*)/MAX(days.operating_days) AS orders_per_operating_hour,
       AVG(o.service_minutes) AS avg_service_minutes
FROM v_order_metrics o JOIN days ON days.weekday=WEEKDAY(o.order_date)
GROUP BY WEEKDAY(o.order_date),HOUR(o.order_time) ORDER BY weekday,hour;

-- Q07: What do server check volumes look like? Active days are NOT hours worked.
SELECT server_id,server_name,COUNT(*) AS orders,COUNT(DISTINCT order_date) AS active_days,
       COUNT(*)/COUNT(DISTINCT order_date) AS orders_per_active_day,
       SUM(net_sales) AS net_sales,SUM(net_sales)/COUNT(*) AS aov
FROM v_order_metrics GROUP BY server_id,server_name ORDER BY server_id;

-- Q08: How do discounted baskets differ? Descriptive; not a causal discount effect.
SELECT CASE WHEN discount_percent>0 THEN 'discounted' ELSE 'full_price' END AS discount_band,
       COUNT(*) AS orders,SUM(net_sales) AS net_sales,SUM(discount_amount) AS discount_amount,
       SUM(net_sales)/COUNT(*) AS aov,
       100*SUM(contribution_amount)/NULLIF(SUM(net_sales),0) AS contribution_margin_pct
FROM v_order_metrics GROUP BY discount_band ORDER BY discount_band;

-- Q09: How do sales and service compare by channel?
SELECT channel,COUNT(*) AS orders,SUM(net_sales) AS net_sales,SUM(net_sales)/COUNT(*) AS aov,
       AVG(service_minutes) AS avg_service_minutes
FROM v_order_metrics GROUP BY channel ORDER BY channel;

-- Q10: What share of recorded orders was cancelled?
SELECT channel,COUNT(*) AS recorded_orders,SUM(status='cancelled') AS cancelled_orders,
       100*SUM(status='cancelled')/COUNT(*) AS cancellation_rate_pct
FROM orders GROUP BY channel ORDER BY channel;

-- Q11: How do daily sales trend? Calendar spine keeps zero-sales dates visible.
WITH RECURSIVE calendar AS (
 SELECT DATE('2026-01-01') AS d UNION ALL
 SELECT d+INTERVAL 1 DAY FROM calendar WHERE d<'2026-06-30'
), daily AS (
 SELECT c.d AS order_date,COALESCE(SUM(o.net_sales),0) AS net_sales
 FROM calendar c LEFT JOIN v_order_metrics o ON o.order_date=c.d GROUP BY c.d
)
SELECT *,CASE WHEN ROW_NUMBER() OVER (ORDER BY order_date)>=7 THEN
       SUM(net_sales) OVER (ORDER BY order_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)
       END AS trailing_7d_net_sales
FROM daily ORDER BY order_date;

-- Q12: How frequently do completed orders include a beverage?
WITH baskets AS (
 SELECT order_id,MAX(category='Beverage') AS has_beverage FROM v_line_metrics GROUP BY order_id
)
SELECT 100*AVG(has_beverage) AS beverage_attachment_pct FROM baskets;

-- Q13: What are seated guest spend and check duration?
SELECT SUM(party_size) AS dine_in_covers,SUM(net_sales)/SUM(party_size) AS dine_in_sales_per_cover,
       AVG(check_duration_minutes) AS dine_in_avg_check_duration_minutes
FROM v_order_metrics WHERE channel='dine_in';
