# AGENTS.md

## Environment

- **Platform**: macOS (darwin)
- **Python**: 3.10+
- **Package manager**: Poetry
- **Working directory**: /Users/andrey/Work/PythonShit/ModelsTrack
- **Git**: initialized
- **Remotes**: `origin` (Gitea), `github` (Baksalyar/aa-models-tracker)

## Project Structure

```
src/models_track/
├── __init__.py      # Package version
├── cli.py           # Entry point (`run()`, `main()`)
├── scraper.py       # Fetch models + model descriptions
├── storage.py       # Read/write data/models.json
└── rss.py           # Write new models to data/feed.xml
.github/
└── workflows/
    └── update-feed.yml  # GitHub Actions cron (every 6h)
```

## Project Description

Track the top 20 AI models from Artificial Analysis leaderboard (https://artificialanalysis.ai/leaderboards/models).

- **Storage**: JSON file (`data/models.json`)
- **RSS output**: `data/feed.xml` — new additions are written as RSS news articles
- **Logic**: Only tracks NEW models entering the top 20. Position changes and model departures are ignored.

## Key Commands

```bash
# Install dependencies
poetry install

# Run the tracker (as a console script)
poetry run models-track

# Or via module
poetry run python -m models_track.cli

# Lint
poetry run ruff check .

# Format check
poetry run ruff format --check .

# Typecheck
poetry run mypy .
```

## CI / Pipeline

Two remotes, different purposes:

| Remote | Branch | Content | Push command |
|--------|--------|---------|--------------|
| `github` | main | Source code only (public) | `git push github main` |
| `origin` (Gitea) | main | Source + private data | `git push origin main` / `./scripts/push-gitea.sh` |

**GitHub Actions** (`.github/workflows/update-feed.yml`):
- Cron: every 6 hours (`0 */6 * * *`)
- Manual: `workflow_dispatch`
- Installs Python 3.12 + Poetry, runs `poetry run models-track`
- Commits `data/feed.xml` and `data/models.json` back to repo
- Job runtime: ~3-5 minutes

**Private files** (gitignored, Gitea only):
- `AGENTS.md` — this file
- `todo.md` — project task list
- `data/models.json` — stored model snapshot
- `data/feed.xml` — RSS feed output

**Pushing private data to Gitea:**
```bash
./scripts/push-gitea.sh
```
This force-adds private files, commits, pushes to Gitea, then resets the local commit so the branch stays clean.

**Important**: never push private files to GitHub. The `.gitignore` prevents accidental inclusion, but always double-check `git status` before pushing.