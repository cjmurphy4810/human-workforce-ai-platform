# Agent 1 — Research Agent (Vertical Slice)

Fetches RSS feeds, deduplicates articles, scores them on 5 consulting-relevant dimensions, persists to SQLite, and generates a dated Markdown Executive Brief — all from a single command.

---

## Quick Start

```bash
cd human-workforce-ai-platform/agent1-research
python main.py
```

Output: `output/YYYY-MM-DD/executive_brief.md`

---

## What It Produces

Every run writes one file:

```
output/
└── 2026-06-28/
    └── executive_brief.md
```

The brief contains five sections:

| Section | Content |
|---|---|
| Executive Summary | Article count, source count, avg score, most active source |
| Top 10 Stories | Ranked by overall score with source and published date |
| Top Consulting Opportunities | Ranked by consulting dimension score |
| Top Podcast Ideas | Ranked by podcast dimension score |
| Source Citations | Full citation table for top 25 articles |

---

## Workflow

```
config.yaml
    │
    ▼
fetcher/rss.py ──► feedparser (per-source, errors isolated)
    │
    ▼
pipeline/deduplicator.py ──► SHA-256 hash, filter against DB
    │
    ▼
storage/repository.py ──► persist new articles (SQLite, async)
    │
    ▼
storage/repository.py ──► load lookback window for brief
    │
    ▼
pipeline/scorer.py ──► 5-dimension keyword scoring
    │
    ▼
pipeline/brief_builder.py ──► Markdown brief
    │
    ▼
output/YYYY-MM-DD/executive_brief.md
```

---

## Configuration

Edit `config/config.yaml` to change sources or scoring weights.

### Adding an RSS source

```yaml
sources:
  - name: My Source
    url: https://example.com/feed.rss
    weight: 0.85       # 0.0–1.0, nudges overall score by ±5%
```

### Scoring weights

Five dimensions — must sum to 1.0:

```yaml
scoring:
  weights:
    business_impact: 0.30
    executive_interest: 0.20
    consulting_opportunity: 0.25
    podcast_potential: 0.15
    urgency: 0.10
```

### Output settings

```yaml
output:
  directory: output     # root directory for brief files
  lookback_days: 7      # articles published within this window appear in brief
  top_stories: 10
  top_consulting: 5
  top_podcast: 5
```

---

## CLI Options

```
python main.py [--config PATH] [--db URL] [--output PATH] [--log-level LEVEL]

--config      YAML config path (default: config/config.yaml)
--db          SQLAlchemy async DB URL (default: sqlite+aiosqlite:///data/research.db)
--output      Output root directory (default: output/)
--log-level   DEBUG | INFO | WARNING | ERROR (default: INFO)
```

Example with PostgreSQL:

```bash
python main.py --db "postgresql+asyncpg://user:pass@localhost:5432/hwai"
```

---

## Running Tests

```bash
# From project root
cd human-workforce-ai-platform
.venv/bin/pytest tests/unit/agent1/ tests/integration/agent1/ -v --no-cov
```

34 tests — unit tests run with zero network/DB access. Integration tests use in-memory SQLite.

---

## Scoring

Each article is scored on 5 keyword-frequency dimensions (0.0–1.0):

| Dimension | Keyword signal |
|---|---|
| Business Impact | revenue, ROI, enterprise, efficiency, cost, workforce |
| Executive Interest | CEO, CTO, board, strategic, governance, leadership |
| Consulting Opportunity | strategy, framework, advisory, compliance, implementation |
| Podcast Potential | breakthrough, innovation, disruption, future, insight |
| Urgency | critical, security, breach, compliance, mandate, risk |

Formula: `min(1.0, keyword_hits / sqrt(term_set_size))` per dimension.
Overall: weighted sum of dimensions, with source `weight` providing ±5% nudge.

---

## Module Map

```
agent1-research/
├── main.py                    CLI entry point
├── config/
│   ├── loader.py              Pydantic config models + YAML loader
│   └── config.yaml            Default sources and weights
├── models/
│   └── article.py             Article, ArticleScore, ScoredArticle
├── fetcher/
│   └── rss.py                 RSS feed fetching (feedparser + asyncio)
├── pipeline/
│   ├── deduplicator.py        SHA-256 hash + filter_new()
│   ├── scorer.py              ScoringEngine (5 dimensions)
│   └── brief_builder.py       Markdown brief generator
└── storage/
    ├── orm.py                 SQLAlchemy ORM (articles table)
    ├── database.py            Engine + session factory + init_db
    └── repository.py          ArticleRepository (async)
```

---

## Default Sources

| Source | Feed type |
|---|---|
| MIT Technology Review | RSS |
| Harvard Business Review | RSS |
| VentureBeat AI | RSS |
| TechCrunch AI | RSS |
| The Verge AI | RSS |
| Wired AI | RSS |
| OpenAI Blog | RSS |
| Google AI Blog | RSS |
| Appian Blog | RSS |

Sources that fail (SSL errors, malformed XML) are logged as warnings and skipped — the run continues.
