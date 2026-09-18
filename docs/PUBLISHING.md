# Deployment architecture

The website is a static application hosted on GitHub Pages. Its deployment workflow is defined in `.github/workflows/deploy-pages.yml`.

## Workflow

| Stage | Responsibility |
|---|---|
| Checkout | Retrieve the repository revision |
| Data preparation | Generate browser data and source downloads from the raw CSVs |
| Validation | Run `tests/test_web.mjs` to verify totals, filters, and export contents |
| Artifact | Package the `dist/` directory |
| Deployment | Publish the validated artifact to the `github-pages` environment |

The workflow is triggered by pushes to `main` or by manual dispatch. The build job reads repository content; the deployment job has Pages and identity-token permissions. Authentication uses the built-in workflow token rather than a committed credential.

Only `dist/` is published as website content. SQL, Python source, and detailed documentation remain available in the repository. The build uses `GITHUB_REPOSITORY` to populate the dashboard's source-code link.

## Reproducibility

The web-data builder uses Python's standard library. Website calculation tests use Node.js and do not require third-party JavaScript packages. Relative asset paths support deployment beneath a repository-specific URL path.

The build checks the fixed dataset's baseline revenue. A replacement dataset requires corresponding updates to validation expectations and written findings; the application is not a general-purpose upload service.

[Web application](WEBSITE.md) · [Analysis setup](SETUP.md)
