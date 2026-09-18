# Data generation and analytical decisions

## Provenance

All data are synthetic, generated using NumPy's seeded random generator (`20260101`). Names and operating assumptions are fictional. The data are not scraped, sampled from a private business, or calibrated to a restaurant benchmark. This synthetic case study was developed with AI assistance.

## Operating assumptions

- One USD location, open all 181 days from January 1 through June 30, 2026; check openings occur from 11:00 through 21:59 in local wall-clock time. No timezone conversion or daylight-saving analysis is performed.
- There are 24 tables: eight two-seat, twelve four-seat and four six-seat tables. Completed dine-in checks occupy a fitting table for the modeled check duration. Cancelled checks release it after five minutes. No overlapping seated checks are generated. If no table fits an attempted dine-in party, no check is recorded; lost demand is not measured.
- Base daily demand is 69 attempts with Poisson variation. Weekday multipliers, Monday–Sunday, are 0.80, 0.83, 0.95, 1.08, 1.43, 1.65 and 1.20. Monthly multipliers are 0.92, 0.96, 1.04, 1.08, 1.16 and 1.20. These deliberately create analysis patterns.
- About 73% of attempted checks are dine-in. Party/portion counts are drawn from 1–6. Takeaway basket size uses the same latent portion distribution, but party_size is blank because a takeaway check does not observe seated guests.
- Each portion receives one main. Beverages, starters and desserts are probabilistic add-ons. Identical items in a check are combined into a single line with quantity. This is a simplified basket model with no substitutions, split bills or partial fulfillment.
- Six rotating staff identifiers handle both seated checks and takeaway payments each day. There are no skill differences, section assignments or staffing hours in the data.
- On Monday–Wednesday, discount probabilities for 0%, 10%, 20% are 65%, 28%, 7%; on other days they are 87%, 11%, 2%. Discounts are not randomized across comparable time periods.
- Prices increase by a modeled 5% on April 1, rounded to the nearest $0.25. Ingredient costs increase by 4% on May 1, rounded to the nearest cent. The menu table holds the final reference values; line snapshots preserve the historical values.
- Cancellation probabilities are 1.3% for dine-in and 2.6% for takeaway. These are pre-fulfillment cancellations with no recognized revenue or ingredient cost. Their attempted basket and intended payment method remain recorded. There are no refunds, post-preparation waste costs, or partial cancellations.
- Service time is a positive, rounded noisy measure centered around 19 minutes, with 8 extra minutes for Friday/Saturday 18:00–19:59 and 3 extra minutes for takeaway. Dine-in check duration is centered around 67 minutes and is always at least 15 minutes longer than first service. These are explicit generation rules, not discovered causal relationships.

## Financial contract

For each **completed** item line:

```text
gross_sales         = quantity × unit_price_snapshot
discount_amount     = ROUND_HALF_UP(gross_sales × discount_percent / 100, 2)
net_sales           = gross_sales − discount_amount
ingredient_cost     = quantity × unit_cost_snapshot
contribution_amount = net_sales − ingredient_cost
```

The order discount applies uniformly to every line, and the project rounds the discount per line before calculating net sales. Do not substitute rounding at the order level. Pandas derives integer cents with `(gross_cents * percent + 50) // 100`; MySQL uses DECIMAL and ROUND on positive amounts. A $2.25 line at 10% discount has a $0.23 discount and $2.02 net sales. Currency summaries retain cents; display formatting may show rounded dollars.

Orders and line facts exclude cancelled checks for all sales, unit and contribution metrics. Cancellation analysis uses the original orders table and includes both statuses. No customer acquisition, repeat-customer or retention metrics can be calculated.

AOV divides total net sales by completed orders. Category contribution margin divides total contribution by total net sales; it is not the mean of line margins. Beverage attachment is the proportion of completed checks containing at least one beverage, not the proportion of guests ordering a beverage. Dine-in covers sum party_size only on completed dine-in checks.

## Time and denominators

Monthly sales per day use calendar days because the fictional restaurant is open every day. Weekday and hourly rates use every occurrence of the weekday in the full reporting calendar, not just high-activity dates. Monday=0 and Sunday=6. In this delivered dataset, all dates and weekday/hour cells contain completed orders. Python validation enforces full date coverage; the MySQL daily and weekday queries explicitly generate the reporting calendar. If analyzing another dataset with closures or missing days, add an operating calendar and revisit the Python daily rolling calculation rather than treating absent dates as zero without investigation.

Trailing seven-day sales are null for the first six dates and cover exactly seven dates thereafter. Month-over-month growth is null in January because no December data are provided. Server active days mean distinct dates with at least one completed check, not shifts worked. Service averages are calculated at order grain, so large baskets do not get more weight.

## What this analysis cannot establish

Revenue growth blends demand, price, basket mix and discount changes. Discount comparisons do not measure uplift or price elasticity. Staffing comparisons do not control for exposure or worker performance. Proposed recommendations have not been implemented, and no savings or profit improvements were measured. Real operational recommendations would require labor hours, section allocation, waste, cost accounting, customer feedback and a designed intervention test.
