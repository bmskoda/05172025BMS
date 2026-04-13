# AGENTS.md

## Cursor Cloud specific instructions

### Overview

AEGIS Forensic Platform v16.0.0 — a monorepo with two components:

| Component | Path | Stack |
|---|---|---|
| **Python backend** (CLI + library) | `/workspace/aegis/` | Python 3.10+, asyncio, aiohttp |
| **React dashboard** (standalone SPA) | `/workspace/dashboard/` | React 19, Vite 8, Tailwind CSS 4 |

The dashboard uses static mock data (`dashboard/src/data/`) and does **not** call the backend at runtime — the two are independently runnable.

### Running services

| Service | Command | Notes |
|---|---|---|
| Python tests | `python3 -m pytest` from repo root | 254 tests, ~1s. Uses `pytest-asyncio`. |
| Dashboard dev server | `cd dashboard && npm run dev` | Vite on port 5173 |
| Dashboard lint | `cd dashboard && npx eslint .` | 2 pre-existing `no-unused-vars` errors in committed code |
| Dashboard build | `cd dashboard && npm run build` | Produces `dashboard/dist/` |
| CLI help | `python3 -m aegis --help` | Confirms package is installed correctly |

### Caveats

- Use `python3` not `python` (no `python` symlink exists in the default environment).
- `~/.local/bin` must be on `PATH` for `pytest` and other pip-installed scripts to be found directly. The update script handles this.
- CLI commands that contact external APIs (`aegis health`, `aegis status`, `aegis investigate`) will hang/timeout without API keys set. This is expected — all external integrations are optional and degrade gracefully.
- No Docker, docker-compose, Makefile, or devcontainer configuration exists in this repo.
- The `dashboard/package-lock.json` lockfile is present — always use `npm install` (not pnpm/yarn).
