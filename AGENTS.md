# AGENTS.md

## Cursor Cloud specific instructions

### Repository overview

This is a **GitHub Skills tutorial** ("Introduction to GitHub"), not an application. It contains GitHub Actions workflows (`.github/workflows/`) and step-by-step Markdown instructions (`.github/steps/`) that guide learners through creating branches, committing files, opening PRs, and merging. There is no application code, no package manager, and no build system.

### Lint and validation commands

| Tool | Command | Purpose |
|---|---|---|
| actionlint | `actionlint` | Lint GitHub Actions workflow YAML for correctness and security |
| yamllint | `yamllint .github/workflows/` | Check YAML syntax and style |
| markdownlint | `markdownlint '**/*.md'` | Lint Markdown files |

All three tools are installed globally. `yamllint` is at `~/.local/bin/yamllint` (ensure `~/.local/bin` is on `PATH`).

### Important caveats

- The workflows reference `skills/exercise-toolkit@v0.1.0` reusable workflows that only run on GitHub.com. They cannot be executed locally.
- `actionlint` reports one pre-existing security warning about untrusted `github.event.pull_request.title` in `3-open-a-pull-request.yml`. This is part of the upstream template.
- `yamllint` and `markdownlint` report pre-existing style issues (line-length, missing `---`, inline HTML). These are upstream and should not be "fixed" unless the tutorial maintainers choose to.
- There is no test suite, build step, or local server to run. Validation is done entirely via the lint tools above.
