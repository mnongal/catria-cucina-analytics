# Web application

The Catria & Cucina dashboard presents the restaurant case study as an interactive browser application. It uses the project's fixed synthetic dataset; arbitrary file uploads are not supported.

## Application views

| View | Content |
|---|---|
| Overview | Sales, completed checks, average spend, contribution margin, revenue mix, leading items, and weekday demand |
| Menu performance | Searchable item table with sales, units, ingredient contribution, and margin rankings |
| Operations | Service times, cancellations, and weekday/hour demand |
| Findings & methods | Full-period business findings, metric definitions, assumptions, and limitations |

Month, channel, and category filters update the analytical views. The findings section describes the full six-month case study and is labeled independently of the active filters.

## Architecture

The application is built with HTML, CSS, and JavaScript modules. `scripts/build_web_data.py` converts the raw CSV tables into `dist/data.json` using Python's standard library. Financial line values are stored as integer cents.

The browser loads the dataset once. `dist/model.mjs` filters records and aggregates metrics; `dist/app.mjs` renders charts, tables, and export controls. There is no application server, database connection, authentication, or external chart service at runtime.

| File | Responsibility |
|---|---|
| `dist/index.html` | Page structure, navigation, and written findings |
| `dist/styles.css` | Responsive layouts and visual styles |
| `dist/model.mjs` | Filter validation, aggregation, and CSV serialization |
| `dist/app.mjs` | UI state, chart rendering, search, sorting, and downloads |
| `dist/data.json` | Generated transaction and menu data |
| `scripts/build_web_data.py` | Reproducible web-data and download preparation |
| `tests/test_web.mjs` | Financial reconciliation and filter tests |

## Downloads

The Project files panel provides the four source CSV tables and data dictionary, the SQL analysis, and the methodology. Export summary generates a CSV for the active month, channel, and category filters. Menu search and sorting affect only the displayed menu table, not the exported population.

## Presentation and accessibility

The interface adapts to desktop and phone screens. Controls have labels and keyboard focus indicators; charts include textual descriptions. Wide menu and hourly tables scroll within their panels. The layout respects reduced-motion preferences.

## Validation and scope

Website checks reconcile full-period totals to the Pandas outputs and independently verify a combined month/channel/category selection against raw CSV rows. Additional checks cover calendar denominators, invalid filters, empty results, and CSV quoting. Browser review covered navigation, filtering, search, sorting, and responsive layouts.

The embedded preview did not expose a download event for the generated summary CSV; export contents were tested separately. Full-period findings and baseline checks are specific to the included synthetic dataset.

[Dashboard metrics](DASHBOARD_GUIDE.md) · [Methodology](METHODOLOGY.md) · [Reproduction](SETUP.md) · [Deployment architecture](PUBLISHING.md)
