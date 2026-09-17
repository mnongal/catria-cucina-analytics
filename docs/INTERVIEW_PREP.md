# Learn the project and discuss it accurately

## A project introduction

“This is a restaurant analytics portfolio case using synthetic transactions. It connects order headers, item lines, menu data and staff identifiers. The analysis calculates net sales and ingredient contribution, examines demand by time, and compares promotions descriptively. The main technical choices are correct table grain, historical price snapshots, consistent rounding and independent reconciliation.”

Adapt this to your own actual work. The initial package was assembled with AI assistance. Do not describe it as a paid client engagement, claim that recommendations were implemented, or say you independently wrote or validated components you have not reviewed.

## Questions to be ready for

**Why four tables?** Orders hold check-level attributes, lines hold item quantities and snapshots, and dimensions avoid repeating item names and staff labels in the source transactions. One order has many lines.

**What is the easiest way to double-count?** Join orders to lines and count rows as orders, or sum a check-level total repeated on every line. The order view aggregates line financials before joining order attributes. For item-filtered order counts, use distinct order IDs.

**Why not use menu_items.selling_price?** Menu prices changed in April. Today's menu reference would restate older transactions. Each line carries its transaction-date unit price and cost.

**What does contribution mean here?** Net sales less modeled ingredient costs. It excludes labor, rent, waste and other expenses, so the 66.08% margin is not a net profit margin.

**How are discounts rounded?** Compute gross for each line, round the discount half up to cents, then subtract. Sum the results to the check. Python uses integer cents; MySQL uses exact DECIMAL arithmetic. See the small rounding test.

**Why is February not necessarily a decline in demand?** Total sales were lower than January, but the month had fewer days. Daily sales increased. This is descriptive in a designed dataset; it is not a real seasonal estimate.

**Should the restaurant remove discounts?** These comparisons cannot answer that. Discounts were more likely on certain weekdays, and baskets differ. A comparable randomized test with contribution per eligible customer would help estimate incremental effects.

**Can you identify the best employee?** No. Revenue totals do not control for time worked, section size or customer mix. The data contain anonymous rotating staff identifiers, not a real performance study.

**How was quality checked?** Primary and foreign keys, valid categories, dates, required/null fields, table capacity and occupancy; financial identities; separate SQLite aggregation; round-half-up and cancelled-order tests. Native MySQL validation remains pending until the included verifier runs successfully against a real MySQL instance.

**What would you collect next?** Labor shifts, table sections, waste and refunds, item stock-outs, and guest feedback. Customer identifiers would need an appropriate consent and privacy design before retention analysis.

## A practical learning route

1. Open all four raw CSVs. Trace a single order_id and calculate its net sales manually.
2. Read `03_views.sql`; explain each join and each result's grain out loud.
3. Recreate Q01, Q03 and Q05 without looking at the answers. Reconcile your results.
4. Read the Pandas merges and `validate='many_to_one'`. Explain why duplicate dimensions are a problem.
5. Run the tests and inspect the rounding edge case and independent SQLite calculation.
6. Set up MySQL, execute imports, inspect warnings, and run the MySQL verifier.
7. Change one chart or add a business question yourself and document what you learned.

## Honest application wording

Before you have reviewed the implementation, describe this as an **AI-assisted portfolio case study under review**, rather than evidence of independent mastery. After you have reproduced the analysis and can defend it, a possible project bullet is:

“Analyzed 15,102 synthetic restaurant checks across six months using SQL and Pandas; reconciled line-level revenue and developed a dashboard covering sales, menu contribution and service demand.”

Use that wording only if it accurately describes your work. Do not claim a revenue uplift, cost saving, customer outcome or employer relationship from this simulated case.
