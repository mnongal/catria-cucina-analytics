# Dashboard metrics and filter behavior

The project includes an interactive web dashboard and a static overview image at `reports/figures/dashboard.png`. Both use the same financial definitions. The static image summarizes the full period; the website recalculates metrics for the selected filters.

## KPI definitions

| Metric | Definition | Population |
|---|---|---|
| Net sales | Historical line gross sales minus rounded line discounts | Matching completed item lines |
| Completed checks | Distinct order IDs | Completed checks containing matching items |
| Average check | Net sales divided by completed checks | Entire menu selected |
| Category spend per check | Selected-category net sales divided by matching checks | A category selected |
| Ingredient contribution | Net sales minus historical ingredient costs | Matching completed item lines |
| Contribution margin | Total contribution divided by total net sales | Matching completed item lines |
| Average service time | Mean service time at check grain | Matching completed checks |
| Cancellation rate | Cancelled checks divided by all recorded checks | Selected month and channel; category ignored |

Ingredient contribution excludes labor, rent, waste, and other operating expenses. It is not operating profit.

## Filters and aggregation

- **Month:** All six months or one month in January–June 2026. The sales chart switches between monthly and daily totals.
- **Dining channel:** All channels, dine-in, or takeaway.
- **Menu category:** Entire menu, mains, starters, beverages, or desserts.

A category filter limits sales to matching lines. Order counts remain distinct check counts, and average spend becomes category spend per matching check. Service time is averaged once per matching check, avoiding extra weight for large baskets.

The menu search and sort controls operate on the displayed item table. They do not change the headline metrics or summary export. Written findings always refer to the full dataset and are labeled accordingly.

## Demand denominators

Weekday demand equals matching completed checks divided by the number of occurrences of that weekday in the selected period. Each hourly cell uses the same weekday denominator. Every calendar date counts because the restaurant is modeled as open daily, including dates with no matching items.

Service time means time to first main served for dine-in and time to ready for takeaway. These different service definitions are relevant when comparing channels.

## Data grain and units

`order_metrics.csv` contains one row per completed check; `line_metrics.csv` contains one row per completed item line. Summary tables are separate aggregations of the same underlying sales and are not additive across tables.

Fact columns ending in `_cents` use integer cents. Summary currency fields use USD. Fields ending in `_pct` contain percentage points: 66.08 represents 66.08%. Ratios must be calculated from matching totals rather than averaged across groups.

## Full-period reconciliation

| Control total | Expected result |
|---|---:|
| Net sales | $1,126,292.82 |
| Completed checks | 14,860 |
| Average order value | $75.79 |
| Ingredient contribution margin | 66.08% |

The browser's headline sales card rounds to whole dollars for display; item tables and exports retain cents. No native Power BI or Tableau workbook is included.

[Data dictionary](DATA_DICTIONARY.md) · [Calculation methodology](METHODOLOGY.md) · [Web application](WEBSITE.md)
