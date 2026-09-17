# Upload the project

**The package now includes an interactive website.** After uploading the files below, follow [Website publishing](WEBSITE.md) to enable GitHub Pages and run the included publishing workflow. Include the `.github` folder when uploading.

1. Extract the ZIP. Open the `restaurant-revenue-analytics` folder.
2. Create an empty repository in your GitHub account, for example `restaurant-revenue-analytics`.
3. Upload the **contents** of this folder, so README.md, data, sql, scripts and docs sit directly at repository root. Do not upload only the ZIP or nest the full project an extra level down.
4. For a local Git workflow, run the following from this folder, substituting your actual account and repository URL:

```bash
git init
git add .
git commit -m "Add restaurant analytics portfolio case study"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/restaurant-revenue-analytics.git
git push -u origin main
```

This assumes the remote repository is empty. If it already contains work, integrate it with your normal Git workflow rather than replacing it.

Suggested repository description: **SQL and Python restaurant analytics case study with synthetic POS data, reproducible KPIs and a dashboard.**

Suggested topics: `sql`, `mysql`, `python`, `pandas`, `data-analysis`, `portfolio`, `synthetic-data`.

Check that the dashboard image and documentation links render after upload. Keep the synthetic-data and AI-assistance disclosures. You can upload first and work through the interview guide afterward; before describing any component as your own demonstrated skill, reproduce it and be ready to explain it.

No account credentials are part of the package. Do not commit database passwords, environment files or a local virtual environment. The included .gitignore covers common local artifacts.
