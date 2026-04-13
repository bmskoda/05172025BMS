# AGENTS.md

## Cursor Cloud specific instructions

### Repository overview

This is a **GitHub Skills "Introduction to GitHub"** tutorial repository. It contains **no application code** — only GitHub Actions workflow YAML files (`.github/workflows/`) and Markdown step instructions (`.github/steps/`). The tutorial teaches Git basics (branches, commits, PRs) via automated GitHub Actions that validate learner progress.

### Linting

Three linting tools are available and should be run from the repo root:

| Tool | Command | Scope |
|------|---------|-------|
| `yamllint` | `yamllint .github/workflows/` | YAML syntax and style for workflow files |
| `markdownlint` | `markdownlint '**/*.md'` | Markdown style for all `.md` files |
| `actionlint` | `actionlint` | GitHub Actions workflow correctness and security |

**Note:** Pre-existing upstream warnings (line-length, truthy, document-start, inline-html) are expected. `actionlint` reports one script-injection warning in `3-open-a-pull-request.yml` (untrusted `github.event.pull_request.title` in inline script) — this is an upstream issue.

### Testing the tutorial flow locally

The tutorial's "application" is a Git workflow. To verify it locally:

1. Create branch `my-first-branch` from `main`
2. Create and commit a `PROFILE.md` file
3. Validate the corresponding workflow files with `actionlint`

The actual GitHub Actions workflows only execute on GitHub.com (they require `secrets.GITHUB_TOKEN` and the GitHub Actions runtime).

### Key caveats

- There are no package managers, build systems, or runtime dependencies.
- There is no dev server or application to start locally.
- All "runs" happen via GitHub Actions on push/PR events on GitHub.com.
- The workflows reference external actions from `skills/exercise-toolkit@v0.1.0` and `skills/action-text-variables@v1`.
