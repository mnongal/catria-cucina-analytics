# Setup and reproduction

Run commands from the repository root, where README.md lives. Use Python 3.11+; the delivered analysis was run with the versions recorded in reports/validation.json. Internet access is needed only to install dependencies, not to generate or analyze data.

## Python

```bash
python -m venv .venv
```

Activate on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell policy blocks activation, use `.\.venv\Scripts\python.exe` in place of `python` in the following commands. No policy change is required.

Activate on macOS/Linux:

```bash
source .venv/bin/activate
```

Then:

```bash
python -m pip install -r requirements.txt
python scripts/analyze.py
python -m unittest discover -s tests -v
```

Optional raw-data regeneration:

```bash
python scripts/generate_data.py
python scripts/analyze.py
```

The seed and dependency versions make raw CSV generation reproducible. Chart pixels can vary with installed fonts; financial results do not. PNG creation uses a system Arial or DejaVu font, falling back to Pillow's default font. No Jupyter installation is needed: `scripts/analyze.py` is the complete Pandas analysis.

## MySQL

Use a local MySQL **8.4** instance, or MySQL 8.0.16+ with enforced CHECK constraints. MySQL is an optional analysis path; Python reproduction works independently.

1. Start the MySQL client **from the repository root**, supplying your existing local MySQL account:

```bash
mysql --local-infile=1 -u YOUR_MYSQL_USER -p
```

2. At the MySQL prompt, inspect local file loading:

```sql
SHOW GLOBAL VARIABLES LIKE 'local_infile';
```

If OFF, a local administrator can enable it for local imports with `SET GLOBAL local_infile=ON;`, or configure `local_infile=ON` under `[mysqld]` and restart their local instance. Only enable this with a trusted local server. The project does not change global server configuration itself.

3. Run in order at the MySQL prompt:

```sql
SOURCE sql/01_schema.sql;
SOURCE sql/02_import.sql;
SOURCE sql/03_views.sql;
SOURCE sql/05_quality_checks.sql;
SOURCE sql/04_analysis.sql;
```

Schema creation intentionally fails if tables already exist; it does not drop or overwrite a database. Do not rerun imports into populated tables. For a separate instance, use a new database name consistently in the SQL files, or manage your disposable database yourself.

Expected raw row counts: servers **12**, menu_items **22**, orders **15,102**, order_items **74,590**. Every import should report zero warnings. LOCAL loading can turn some problems into warnings, so correct counts alone are insufficient; inspect each `SHOW WARNINGS` result and then run the verifier. Null operational fields in orders are blank CSV cells and are converted with `NULLIF`.

If using MySQL Workbench, open and execute the scripts in sequence. Replace the four CSV paths in `02_import.sql` with absolute paths using forward slashes, e.g. `C:/projects/restaurant-revenue-analytics/data/raw/orders.csv`. Workbench's connection may also need `OPT_LOCAL_INFILE=1` under Advanced / Others. Enabling the server setting alone is insufficient; the client must allow LOCAL loading too. These files use UTF-8 with LF endings; `.gitattributes` preserves LF.

## Compare MySQL and Python

After the imports and views exist:

```bash
python -m pip install -r requirements-mysql.txt
python scripts/verify_mysql.py --user YOUR_MYSQL_USER
```

Password entry is prompted and is not written to the repository. Optional arguments: `--host`, `--port`, `--database`. The verifier reads the existing tables/views, checks row counts, executes all 13 analysis queries, and compares matching columns to the CSV/JSON outputs. It makes no table changes. A mismatch raises an error; success writes `reports/mysql_validation.json` with the server version and comparison results. Rerun `analyze.py` before verifying if raw CSVs changed, and ensure the database contains those same raw CSVs.

## Troubleshooting

- `ModuleNotFoundError`: install requirements with the same Python interpreter used to run the scripts.
- LOCAL INFILE disabled/rejected: confirm both server and client settings above. Use absolute file paths if working directory resolution fails.
- Duplicate-key errors or import warnings: stop; confirm you are using empty project tables and unmodified CSVs. Do not disable foreign keys to hide errors.
- Results differ: confirm completed-only filters, historical snapshot prices, round-half-up line discounts, and weighted ratio definitions.

References: [MySQL loading data](https://dev.mysql.com/doc/refman/8.4/en/loading-tables.html), [LOCAL controls](https://dev.mysql.com/doc/refman/8.4/en/load-data-local-security.html).

## Website preview

The static application can be served from repository root:

```bash
python scripts/build_web_data.py
python -m http.server 8765 --bind 127.0.0.1 --directory dist
```

The local preview is available at `http://127.0.0.1:8765/`. Web calculation checks run with `node tests/test_web.mjs` (Node.js 20+). The included browser data are ready to serve; rebuilding is needed after changing source CSVs. Baseline checks and written findings must also be reviewed when changing the dataset.
