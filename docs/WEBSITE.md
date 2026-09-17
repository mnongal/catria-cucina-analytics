# Interactive website · GitHub Pages

The repository now includes a complete interactive website in `dist/`. It contains an overview, menu performance table, demand heatmap, findings, metric definitions and downloadable project files. Visitors can filter month, dining channel and item category, search and sort the menu, and export the current summary as CSV. It works on desktop and phone screens.

**GitHub Pages hosts the website. GitHub Actions publishes updates to Pages.** This is a static website: calculations happen in the visitor's browser using synthetic data generated from the included CSVs. Visitors do not need Python, MySQL or a login. No database password or hosted database is needed. There are no paid APIs, external fonts, analytics trackers or third-party chart dependencies.

## Publish for the first time

1. Create a new **public** GitHub repository named `restaurant-revenue-analytics`. Public repositories can use GitHub Pages on GitHub Free. Leave GitHub's starter README, license and .gitignore options unchecked; this package already contains those files.
2. Extract the updated project ZIP. Upload the **contents** of the `restaurant-revenue-analytics` folder at repository root, including the `.github` folder. Do not upload the ZIP itself or nest the project inside another folder. The root should show `README.md`, `dist`, `scripts`, `data`, `tests`, and `.github` among the other project folders. Use the `main` branch.
3. Open **Settings → Pages**. Under **Build and deployment**, choose **GitHub Actions** as the source.
4. Open **Actions → Publish restaurant dashboard → Run workflow → main → Run workflow**. If an earlier run failed before Pages was enabled, run it again now.
5. Wait for both `build` and `deploy` to succeed. Open the URL on the deployment result or in **Settings → Pages**. It will normally have the shape `https://YOUR-USERNAME.github.io/restaurant-revenue-analytics/`.
6. Add that actual URL to the repository's **About → Website** field, and pin the repository on your GitHub profile.

Do not choose GitHub's Jekyll starter workflow or publish the repository root as website content. The supplied workflow publishes only `dist/`, and regenerates its dataset from raw CSVs first. Each later push to `main` runs the same checks and deploys the updated website automatically.

### If the `.github` folder was missed

Verify the repository contains `.github/workflows/deploy-pages.yml`. File managers can hide dot-prefixed folders. Enable hidden items before uploading, or use Git to upload the complete project. You can also use **Add file → Create new file**, enter `.github/workflows/deploy-pages.yml`, and paste the content of the included file. The workflow must exist at that exact repository path to appear under Actions.

### What the workflow does

1. Checks out the repository.
2. Runs `python3 scripts/build_web_data.py` using only the Python standard library.
3. Runs `node tests/test_web.mjs` to check financials, denominators and filters.
4. Packages `dist/` and deploys it to GitHub Pages.

It uses GitHub's standard Pages actions and the built-in workflow token, scoped to reading repository content and deploying Pages. It requires no manually created token, password or secret. The repository link on the website is populated from GitHub's `GITHUB_REPOSITORY` environment variable during the build.

## Preview locally

From repository root:

```bash
python scripts/build_web_data.py
python -m http.server 8765 --bind 127.0.0.1 --directory dist
```

Open `http://127.0.0.1:8765/` in a browser. Keep the terminal open while previewing; press Ctrl+C when finished. Double-clicking index.html directly is not supported because browsers restrict loading JSON and JavaScript modules through file URLs.

The data and download ZIP are already included, so the second command alone can preview the delivered version. The Python build step is required after changing raw data. This build intentionally checks the case study's baseline total and fails if data change; review and update the validation expectations and written findings for a new dataset.

## Metric behavior

- Entire-menu view: completed checks, whole-check sales and AOV.
- Category view: selected line sales, distinct checks containing those items, and selected-category spend per matching check. It does not call the selected-category subtotal the whole basket's value.
- Demand and service use matching distinct completed checks; large baskets do not receive more weight.
- Weekday/hour denominators count every applicable date, including dates with no matching items. All days are modeled as open.
- Cancellation rate always uses all recorded checks within period and channel; category is explicitly ignored.
- The Findings & methods view describes the full case-study period and says so. Its editorial findings do not pretend to change with the filters.
- Whole-dollar cards are rounded for display; menu tables and exports retain cents. Financial calculations use integer cents.
- Export summary includes all items matching the three main filters. The menu text search and sort only change the visible table, not the main KPI population or export.

## Validation

The website calculation tests compare all-period KPIs to the Pandas output, reconcile time and menu totals, check calendar denominators, and independently check an April/takeaway/dessert selection against raw CSV rows. They also cover invalid filters and empty results. See `reports/web_validation.json` for the checks performed on the delivered website.

Native GitHub Actions deployment has not run until the project is uploaded to your repository and Pages is enabled. A local preview is not a public deployment. Native MySQL execution remains separately pending, as documented in the main README.

## Source files

- `dist/index.html` — semantic page structure and findings.
- `dist/styles.css` — responsive theme and layout.
- `dist/app.mjs` — rendering, controls, export and optional browser-agent tools.
- `dist/model.mjs` — filter validation and financial aggregation.
- `dist/data.json` — compact generated data; monetary line fields are integer cents.
- `scripts/build_web_data.py` — builds data and source downloads from CSVs.
- `tests/test_web.mjs` — independent checks, runnable with Node.js 20+.
- `.github/workflows/deploy-pages.yml` — build, check and publish workflow.

Official references: [GitHub Pages custom workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages), [configure a publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).
