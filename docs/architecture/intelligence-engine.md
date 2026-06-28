# Executive Intelligence Engine — Architecture

## Purpose

The Intelligence Engine converts raw research from the Research Plugin into
prioritized executive decision support. It is a read-only consumer of the
research database and produces five output files consumed by the API and dashboard.

---

## Plugin Boundaries

```
Core Platform (FastAPI)
│
├── Research Plugin (agent1-research/)      ← produces research.db + executive_brief.md
│   └── ArticleRepository                  ← READ ONLY from Intelligence Engine
│
└── Intelligence Engine (intelligence-engine/)  ← THIS PLUGIN
    ├── Analyzers                           ← business rules
    ├── Engines                             ← scoring strategies
    ├── Pipeline                            ← orchestration
    └── Output                             ← JSON + Markdown files
```

**The Intelligence Engine never writes to the research database.**
**The Research Plugin has no knowledge of the Intelligence Engine.**
Replacing either plugin requires no changes to the other.

---

## Internal Architecture

```
intelligence-engine/intelligence/
├── config/defaults.py          ← all tunable thresholds in one place
├── models/intelligence.py      ← ArticleData + all output types (no research imports)
├── analyzers/
│   ├── opportunity_detector.py ← 6 opportunity types
│   ├── trend_detector.py       ← 7 trend types
│   └── impact_analyzer.py      ← 8 executive impact dimensions
├── engines/
│   ├── scoring_engine.py       ← pluggable ScoringStrategy protocol + registry
│   └── recommendation_engine.py← per-article action assignment
├── pipeline/
│   └── intelligence_pipeline.py← single entry point, assembles IntelligenceReport
└── output/
    └── writer.py               ← writes 5 JSON + 1 Markdown file
```

### Data Flow

```
ArticleRepository (research.db)
        │
        │  GET /intelligence/run
        ▼
  [API layer converts ScoredArticle → ArticleData]
        │
        ▼
  IntelligencePipeline.run()
    ├── OpportunityDetector    → list[Opportunity]
    ├── TrendDetector          → list[Trend]
    ├── ImpactAnalyzer         → list[ExecutiveImpact]
    └── RecommendationEngine   → list[Recommendation]
        │
        ▼
  OutputWriter
    ├── executive_intelligence.json
    ├── executive_intelligence.md
    ├── executive_recommendations.json
    ├── trend_analysis.json
    └── consulting_pipeline.json
        │
        ▼
  API Endpoints (read from files)
    GET /intelligence
    GET /intelligence/opportunities
    GET /intelligence/recommendations
    GET /intelligence/trends
    GET /intelligence/consulting
    GET /intelligence/podcasts
```

---

## Scoring Engine — Pluggable Strategy Pattern

The `ScoringEngine` uses a `Protocol`-based strategy pattern. Implementations
need only satisfy the interface — no base class required.

```python
class ScoringStrategy(Protocol):
    name: str
    def score_articles(
        self,
        articles: list[ArticleData],
        opportunity_type: OpportunityType,
    ) -> list[ArticleScore]: ...
```

### Adding a New Scoring Provider

```python
from intelligence.engines.scoring_engine import ScoringEngine, ScoringStrategy

class ClaudeScoringStrategy:
    name = "claude_opus_v1"

    def score_articles(self, articles, opportunity_type):
        # Call Claude API with article content
        # Return list[ArticleScore]
        ...

engine = ScoringEngine()
engine.register(ClaudeScoringStrategy())

# Use in pipeline:
from intelligence.pipeline.intelligence_pipeline import PipelineConfig, run_intelligence_pipeline
report = run_intelligence_pipeline(articles, config=PipelineConfig(), engine=engine)
```

---

## How AI Providers Consume Intelligence Engine Outputs

The Intelligence Engine outputs are provider-agnostic JSON files. Any AI system
can consume them without modification.

### Claude

```python
import anthropic, json
from pathlib import Path

client = anthropic.Anthropic()
intel = json.loads(Path("intelligence-engine/data/output/2026-06-28/executive_intelligence.json").read_text())

response = client.messages.create(
    model="claude-opus-4-8",
    max_tokens=2000,
    messages=[{
        "role": "user",
        "content": f"Based on this intelligence report, what are the top 3 executive actions?\n\n{json.dumps(intel['summary'])}"
    }]
)
```

### Google NotebookLM

1. Export `executive_intelligence.md` and upload as a NotebookLM source.
2. NotebookLM's grounding will include all opportunities, trends, and recommendations.
3. Generate quizzes, briefings, or audio overviews directly from the intelligence report.

### OpenAI

```python
import openai, json
intel = json.loads(open("executive_intelligence.json").read())
client = openai.OpenAI()
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are an executive strategy advisor."},
        {"role": "user", "content": f"Review this intelligence report and suggest priorities:\n{json.dumps(intel['opportunities'][:5])}"}
    ]
)
```

### Local Models (Ollama / LM Studio)

```bash
# Feed the markdown report directly to a local model
cat executive_intelligence.md | ollama run llama3 "Summarize the top consulting opportunities"
```

### YouTube / LinkedIn Plugins (upcoming)

These plugins will read `executive_recommendations.json` and filter by `action`:
- `action == "youtube_video"` → YouTube Plugin picks up for scripting
- `action == "newsletter"` → LinkedIn Plugin drafts a post
- `action == "podcast"` → ElevenLabs Plugin generates audio

---

## Opportunity Types

| Type | Primary Signal | Business Value |
|------|---------------|----------------|
| Consulting | `consulting_opportunity` ≥ 0.58 | $10K–$500K per engagement |
| Podcast | `podcast_potential` ≥ 0.58 | Audience growth + brand |
| Executive Briefing | `executive_interest` ≥ 0.62 | C-suite relationship pipeline |
| Book | `business_impact` ≥ 0.55, 6+ articles | $5K–$200K + speaking |
| Course | `executive_interest` ≥ 0.55, 4+ articles | $2K–$150K annually |
| LinkedIn Campaign | `executive_interest` + `business_impact` ≥ 0.45 | 2–10 qualified leads |

---

## Trend Types

| Type | Detection Logic |
|------|----------------|
| Emerging | Topic in recent 7 days only, 3+ occurrences |
| Growing | Recent/baseline frequency ratio ≥ 1.8× |
| Declining | Present in baseline, absent/rare in recent |
| Repeated | Sustained presence in both windows |
| Industry Pattern | High `business_impact` articles on same topic |
| Vendor Activity | Bigram contains known vendor name |
| Enterprise Risk | High `urgency` (≥ 0.60) cluster |

---

## Tuning Business Rules

All thresholds are in `intelligence-engine/intelligence/config/defaults.py`.
No code changes are needed to adjust sensitivity:

```python
# Raise consulting threshold to reduce noise:
OPPORTUNITY_THRESHOLDS["consulting"]["min_consulting_score"] = 0.70

# Tighten trend detection:
TREND_MIN_RECENT_COUNT = 5
TREND_GROWTH_RATIO = 2.5
```

---

## Output File Reference

| File | Contents | Updated by |
|------|----------|-----------|
| `executive_intelligence.json` | Full report: summary, opportunities, trends, impact, recommendations | `POST /intelligence/run` |
| `executive_intelligence.md` | Human-readable Markdown version of the full report | `POST /intelligence/run` |
| `executive_recommendations.json` | Per-article action recommendations | `POST /intelligence/run` |
| `trend_analysis.json` | Trends grouped by type | `POST /intelligence/run` |
| `consulting_pipeline.json` | Consulting opportunities only, pipeline format | `POST /intelligence/run` |
