# AGENTS.md

## Cursor Cloud specific instructions

This repository is a **GitHub Skills tutorial** ("Introduction to GitHub"). It contains no runnable application code — only GitHub Actions workflow YAML files (`.github/workflows/`) and Markdown step instructions (`.github/steps/`).

### Repository structure

| Path | Purpose |
|------|---------|
| `.github/workflows/*.yml` | 5 GitHub Actions workflows that automate the exercise steps |
| `.github/steps/*.md` | Markdown content for each exercise step |
| `README.md` | Exercise landing page |

### Linting

Three linting tools are available:

- **actionlint** (`~/go/bin/actionlint`): Semantic linter for GitHub Actions workflows. Run from repo root: `actionlint`
- **yamllint** (`~/.local/bin/yamllint`): YAML syntax/style linter. Run: `yamllint -d relaxed .github/workflows/`
- **markdownlint-cli2**: Markdown linter. Run: `markdownlint-cli2 "**/*.md"`

Ensure `~/go/bin` and `~/.local/bin` are on `PATH` before using `actionlint` or `yamllint`.

### Pre-existing lint warnings

All lint warnings (line-length, inline HTML, etc.) are from the upstream GitHub Skills template. The single `actionlint` finding about untrusted `github.event.pull_request.title` in `3-open-a-pull-request.yml` is also pre-existing.

### Testing

There is no automated test suite. Validation is done via the linting tools above. The workflows themselves run on GitHub Actions (triggered by push/PR events) and cannot be executed locally.

### Hello-world exercise

The tutorial exercise steps are: (1) create branch `my-first-branch`, (2) add `PROFILE.md`, (3) open a PR titled "Add my first file", (4) merge. These are validated by the GitHub Actions workflows when run on GitHub.
