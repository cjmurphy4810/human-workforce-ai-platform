# Agent 1 — Architecture

## Pipeline Flow

```
YAML Config
    │
    ▼
source_manager.py ──► load enabled SourceConfig → ResearchSource list
    │
    ├──[RSS sources]──► rss_manager.py ──► feedparser → ResearchArticle list
    │
    └──[Website sources]──► website_fetcher.py ──► httpx + BS4 → ResearchArticle list
                                                              │
    ┌─────────────────────────────────────────────────────────┘
    ▼
article_deduplicator.py
    │  SHA-256 fingerprint check: in-memory seen set + bulk DB query
    │  Drops duplicates within run and against stored articles
    ▼
topic_classifier.py
    │  Keyword matching against TopicConfig.keywords
    │  Sets article.topic_ids: list[str]
    ▼
scoring_engine.py
    │  9-dimension heuristic scoring (keyword term sets + source weight)
    │  Sets article.score: ArticleScore
    ▼
keyword_extractor.py
    │  Frequency-based top-N token extraction (stopword-filtered)
    │  Sets article.keywords: list[str]
    ▼
repository.py (save_article)
    │  Persists to research_articles via SQLAlchemy async session
    ▼
repository.py (get_articles_since)
    │  Load lookback window of scored articles for briefing
    ▼
insight_generator.py
    │  generate_podcast_ideas     — high podcast_potential articles
    │  generate_consulting_opps   — high consulting_potential + service line inference
    │  generate_linkedin_ideas    — high executive_interest articles
    │  generate_newsletter_ideas  — top overall-score articles
    │  generate_risk_observations — high urgency articles with severity rating
    ▼
keyword_extractor.py (aggregate)
    │  Combined keyword frequency across all top articles
    ▼
topic_ranking_engine.py
    │  Aggregate article scores by topic → TopicScore list (ranked)
    ▼
citation_manager.py
    │  Numbered citation dicts from top_articles
    ▼
ExecutiveBriefing (assembled)
    │
    ├──► repository.py (save_briefing) ──► DB: executive_briefings + briefing_articles
    │
    └──► daily_archive.py
              ├──► markdown_export.py ──► data/archives/{date}/executive_brief.md
              └──► json_export.py     ──► data/archives/{date}/executive_brief.json
```

---

## Scoring Dimensions

Each article receives a float score (0.0–1.0) on 9 dimensions:

| Dimension | Signal |
|---|---|
| `relevance` | Keyword match rate against matched topic keyword lists |
| `business_impact` | Hits against enterprise/revenue/ROI/efficiency terms |
| `consulting_potential` | Hits against strategy/governance/framework/advisory terms |
| `podcast_potential` | Hits against breakthrough/disruption/analysis/insight terms |
| `executive_interest` | Hits against CEO/CTO/CISO/strategic/board/leadership terms |
| `confidence` | Source `confidence_base × weight` (represents source authority) |
| `novelty` | Static 0.7 default (future: inverse of topic saturation) |
| `urgency` | Hits against critical/breach/vulnerability/mandate/emerging terms |
| `overall` | Weighted sum per `scoring.weights` in config |

Weights are validated to sum to 1.0 at config load time.

---

## Database Schema

```
research_sources
  id, name (unique), url, type, topics (JSON), weight,
  confidence_base, enabled, last_fetched_at, article_count, error_count

research_articles
  id, title, url, source_id (FK), source_name, published_at, fetched_at,
  summary, full_text, content_hash (unique, indexed),
  topic_ids (JSON), keywords (JSON),
  score_relevance, score_business_impact, score_consulting_potential,
  score_podcast_potential, score_executive_interest, score_confidence,
  score_novelty, score_urgency, score_overall

executive_briefings
  id, date_label (indexed), generated_at, total_articles_fetched,
  total_articles_scored, total_sources_checked, confidence_score,
  trend_summary, keyword_summary (JSON), topic_scores (JSON),
  podcast_ideas (JSON), consulting_opportunities (JSON),
  linkedin_ideas (JSON), newsletter_ideas (JSON),
  risk_observations (JSON), citations (JSON)

briefing_articles
  id, briefing_id (FK), article_id (FK), rank
```

All reads and writes go through `ResearchRepository`. No raw SQL is used outside `storage/repository.py`.

---

## Extension Points

**Add a scoring dimension:** Add a term frozenset and keyword-score call in `scoring_engine.py`. Update `ScoringWeights` and `ArticleScore` models. Weights must still sum to 1.0.

**Add a source type:** Implement a new fetch function with signature `async def fetch_X(source, fetching) -> list[ResearchArticle]` and add a branch in `orchestrator.py`.

**Add a topic:** Add an entry to `research.topics` in the YAML config. No code changes required.

**Switch to PostgreSQL:** Set `DATABASE_URL=postgresql+asyncpg://...` and uncomment `asyncpg` in `requirements.txt`. Run `alembic upgrade head` from project root.
