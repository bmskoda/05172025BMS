# AGENTS.md

## Overview

This repository is a **GitHub Skills tutorial** ("Introduction to GitHub"). It contains no application code — the entire product is GitHub Actions workflows (`.github/workflows/*.yml`) and Markdown step instructions (`.github/steps/*.md`, `README.md`).

## Cursor Cloud specific instructions

### What this repo contains

- 5 GitHub Actions workflow YAML files in `.github/workflows/`
- Markdown tutorial steps in `.github/steps/`
- A `README.md` with exercise instructions
- No `package.json`, no backend/frontend, no Docker, no database

### Linting

- **GitHub Actions workflows:** `actionlint .github/workflows/*.yml` (requires `actionlint` — install via `go install github.com/rhysd/actionlint/cmd/actionlint@latest`, binary lands in `$(go env GOPATH)/bin`)
- **Markdown:** `markdownlint '**/*.md'` (requires `markdownlint-cli` — install via `npm install -g markdownlint-cli`)
- Pre-existing lint warnings in the repo are from upstream GitHub Skills content (e.g., line-length in `README.md`, inline HTML for badge images). Do not attempt to fix these unless explicitly asked.

### Testing

There is no automated test suite. Validation consists of:

1. YAML syntax validation (e.g., `python3 -c "import yaml; yaml.safe_load(open('file.yml'))"`)
2. `actionlint` for GitHub Actions best practices
3. `markdownlint` for Markdown quality

### Running the "application"

The tutorial runs entirely on GitHub.com via GitHub Actions. There is no local server to start. The exercise flow is: fork/copy repo → create branch `my-first-branch` → commit `PROFILE.md` → open PR → merge PR. Each step triggers a corresponding workflow that validates progress and posts feedback.

### Important gotchas

- `actionlint` needs Go ≥ 1.22; the VM's system Go works but `actionlint@latest` may auto-download a newer toolchain.
- The workflows depend on `skills/exercise-toolkit@v0.1.0` (a reusable workflow hosted on GitHub). This external dependency cannot be validated locally.
- Workflow file `3-open-a-pull-request.yml` has a known `actionlint` warning about `github.event.pull_request.title` being potentially untrusted in an inline script. This is an upstream issue in the GitHub Skills template.
