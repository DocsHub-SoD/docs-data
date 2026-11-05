# Shape of Dreams Modding API Data

Canonical API dataset and knowledge base repository for the game Shape of Dreams.

## Contents
- `api/` — 897 normalized JSON models for all gameplay types.
- `api.db` — Compiled SQLite database for fast indexed SQL queries.
- `api-graph.json` — Knowledge graph mapping class inheritance and dependencies.
- `LLM_GUIDE.md` — Guide and schema for AI agents.
- `scripts/compile_db.py` — Database compilation script executed automatically on CI.

## Community Contributions
You can enhance class summaries, method remarks, and parameter descriptions directly in `api/*.json` and submit a Pull Request. Once merged, `api.db` is rebuilt automatically via GitHub Actions.
