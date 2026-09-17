# Data dictionary

All raw CSVs are UTF-8, comma-delimited, have one header row, and use LF newlines. Blank cells represent NULL only in the documented optional order fields. Monetary values are USD with two decimal places. IDs are integers, not row positions.

## servers — one fictional staff member, 12 rows

| Column | MySQL type | Meaning |
|---|---|---|
| server_id | INT PK | Unique staff identifier |
| server_name | VARCHAR(50) | Anonymous label such as Server 01; no personal information |

## menu_items — one menu item, 22 rows

| Column | MySQL type | Meaning |
|---|---|---|
| item_id | INT PK | Unique item identifier |
| item_name | VARCHAR(80) | Display name |
| category | VARCHAR(20) | Main, Starter, Beverage, Dessert |
| selling_price | DECIMAL(10,2) | End-of-period reference selling price, after April adjustment |
| unit_cost | DECIMAL(10,2) | End-of-period reference ingredient cost, after May adjustment |

Reference prices are useful for menu lookup, not historical revenue calculation.

## orders — one recorded check, 15,102 rows

| Column | MySQL type | Meaning / allowed values |
|---|---|---|
| order_id | INT PK | Unique recorded check; sequence gaps can occur |
| order_date | DATE | Local check opening date, 2026-01-01 through 2026-06-30 |
| order_time | TIME | Local check opening time, 11:00:00–21:59:00 |
| server_id | INT FK | Staff handling check; links to servers |
| table_number | INT NULL | 1–24 for dine-in, blank for takeaway |
| party_size | INT NULL | Seated guests, 1–6; blank for takeaway |
| channel | VARCHAR(12) | dine_in or takeaway |
| status | VARCHAR(12) | completed or cancelled |
| discount_percent | INT | Whole percentage points: 0, 10 or 20 |
| payment_method | VARCHAR(20) | Credit Card, Debit Card or Cash; intended method on cancellations |
| service_minutes | INT NULL | Dine-in time to first main served, or takeaway time to ready; blank on cancellations |
| check_duration_minutes | INT NULL | Dine-in time until check/table release, or takeaway time to ready; blank on cancellations |

Service time is not table occupancy. Duration can extend past the last check-opening hour. There is no customer ID or explicit booking record.

## order_items — one distinct item on a check, 74,590 rows

| Column | MySQL type | Meaning |
|---|---|---|
| order_item_id | INT PK | Unique item line |
| order_id | INT FK | Parent recorded check |
| item_id | INT FK | Menu item |
| quantity | INT | Positive whole count of this item |
| unit_price | DECIMAL(10,2) | Selling-price snapshot at order date |
| unit_cost | DECIMAL(10,2) | Ingredient-cost snapshot at order date |

The `(order_id, item_id)` pair is unique. Cancelled checks retain attempted lines; filter by status before recognizing any economics.

## Processed outputs

`order_metrics.csv` is one row per **completed order**; `line_metrics.csv` is one row per **completed item line**. Both include derived integer `_cents` columns. Divide them by 100 when displaying dollars. Never treat cents as dollar amounts.

Summary CSVs already use dollars: `gross_sales`, `net_sales`, `discount_amount`, `cost_amount`, `contribution_amount`. Here `cost_amount` equals modeled ingredient cost. `aov` is dollars per completed check. `contribution_margin_pct`, `mom_net_sales_pct`, and `cancellation_rate_pct` are percentage points (66.08 means 66.08%); divide by 100 before applying a BI percent format. Summary numbers are exported to six decimals to preserve ratios; monetary totals still reconcile to cents.

| Output | Grain / keys | Additional fields |
|---|---|---|
| monthly_kpis.csv | month (YYYY-MM) | calendar_days; net_sales_per_day; mom_net_sales_pct, first month blank |
| daily_kpis.csv | order_date | trailing_7d_net_sales, first six days blank |
| menu_performance.csv | item_id | item_name, category, units, contribution_per_unit |
| category_performance.csv | category | units and weighted contribution_margin_pct |
| weekday_performance.csv | weekday (0=Mon) | day_name, operating_days, orders_per_day |
| hourly_demand.csv | weekday, hour | operating_days, orders_per_operating_hour |
| server_performance.csv | server_id | server_name, active_days, orders_per_active_day |
| discount_performance.csv | discount_band | discounted / full_price |
| channel_performance.csv | channel | completed order economics and avg_service_minutes |
| cancellations.csv | channel | recorded_orders, cancelled_orders, cancellation_rate_pct |
| kpis.json | one object for full period | Complete headline financial, cancellation, guest and attachment metrics |

Common summary `orders` fields count completed checks. Ratios and averages are non-additive: recompute them from underlying amounts/counts for a new grouping. Raw row counts and seed are in `data/raw/manifest.json`.
