# Build on the included dashboard

`reports/figures/dashboard.png` is a finished static dashboard generated from the Python results. It can be used directly in the README or a portfolio presentation. It is not an interactive BI application or evidence of using Power BI/Tableau.

## Option A: Build quickly with summaries

Import `monthly_kpis.csv`, `menu_performance.csv`, `weekday_performance.csv` and `category_performance.csv` as separate summary tables. Use each table for its corresponding chart, as shown in the PNG. Do not join summaries to one another or add their totals together: they are different aggregations of the same sales.

Use separate cards populated from `kpis.json`, or calculate cards from monthly totals. Net sales is SUM(net_sales), completed checks is SUM(orders), AOV is SUM(net_sales)/SUM(orders), and margin is SUM(contribution_amount)/SUM(net_sales). Do not average monthly AOV or margin for a full-period card.

Suggested charts: monthly net sales columns; top-five item sales horizontal bars; completed checks per operating weekday; weighted category contribution margin. Keep USD units visible and make synthetic provenance visible.

## Option B: Add consistent filters with facts

Use `order_metrics.csv` as your completed-check fact and `line_metrics.csv` as the completed-item fact. Create a date dimension and a menu dimension from raw `menu_items.csv`. Relate date → orders (one-to-many), orders → lines on order_id (one-to-many), and menu → lines on item_id (one-to-many), using single-direction filtering. Server and channel filters should apply at order level. Avoid a second active date → lines path that would create ambiguity.

Calculate sales from `net_cents / 100` and contribution from `contribution_cents / 100`. Order counts at line grain must use DISTINCTCOUNT(order_id); averaging service_minutes from lines weights multi-line checks too heavily. An item filter affects line-level sales and distinct checks containing those items. It does not automatically filter order-level cards through a single-direction relationship; keep such cards labeled for all checks or implement a deliberate measure using the filtered order ID set.

For cancellation visuals, use raw orders as a **separate fact** because completed facts omit cancelled checks. Share date and channel dimensions deliberately; do not join raw orders to completed orders as if both represented identical populations.

## Formatting and validation

- Parse order_date as a date, month as a month-start date or chronologically sorted YYYY-MM label, hour/weekday as whole numbers.
- Format dollar fields as currency; quantity and order counts as integers.
- Ratio fields ending `_pct` already contain percentage points. Divide by 100 for BI percentage formatting. A new measure contribution/net is already a fraction and needs no further division.
- When changing date range, recompute operating-day denominators from a date calendar. Do not reuse the six-month `orders_per_day` values for a filtered period.
- Before adding filters, reconcile total net sales to **$1,126,292.82** and completed orders to **14,860**. AOV should be **$75.79** and contribution margin **66.08%**.
- Document whether each visual uses all recorded checks or completed checks. Do not label ingredient contribution as net profit.

No native .pbix or Tableau workbook is included; the CSVs are the portable starting point.
