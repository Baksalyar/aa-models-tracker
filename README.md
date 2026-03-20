# AA Models Tracker

Tracks the top 20 AI models from the [Artificial Analysis LLM Leaderboard](https://artificialanalysis.ai/leaderboards/models) and publishes changes as an RSS feed.

## How it works

- Scrapes the leaderboard page (parsed from Next.js RSC data)
- On first run: saves top 20 models to `data/models.json` and generates RSS entries
- On subsequent runs: diffs against stored data, writes new additions to `data/feed.xml`
- Each RSS entry includes the model description scraped from its individual page

## Setup

```bash
poetry install
```

## Run

```bash
poetry run models-track
```

Or:

```bash
poetry run python -m models_track.cli
```

## Output

- `data/models.json` — current top 20 snapshot
- `data/feed.xml` — RSS feed with new model announcements

RSS entry format:

```xml
<item>
  <title>New model: GPT-5.4 from OpenAI, intel index 57.17</title>
  <link>https://artificialanalysis.ai/models/gpt-5-4</link>
  <description>GPT-5.4 is amongst the leading models in intelligence...</description>
</item>
```

## Automation

GitHub Actions runs every 6 hours (cron `0 */6 * * *`) and can be triggered manually from the Actions tab.

## Development

```bash
poetry run ruff check .
poetry run ruff format --check .
poetry run mypy src/
```
