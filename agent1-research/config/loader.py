from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field, model_validator


class SourceConfig(BaseModel):
    name: str
    url: str
    weight: float = 1.0


class ScoringWeights(BaseModel):
    business_impact: float = 0.30
    executive_interest: float = 0.20
    consulting_opportunity: float = 0.25
    podcast_potential: float = 0.15
    urgency: float = 0.10

    @model_validator(mode="after")
    def weights_sum_to_one(self) -> ScoringWeights:
        total = round(
            self.business_impact
            + self.executive_interest
            + self.consulting_opportunity
            + self.podcast_potential
            + self.urgency,
            6,
        )
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Scoring weights must sum to 1.0, got {total}")
        return self


class ScoringConfig(BaseModel):
    weights: ScoringWeights = Field(default_factory=ScoringWeights)


class OutputConfig(BaseModel):
    directory: str = "output"
    lookback_days: int = 7
    top_stories: int = 10
    top_consulting: int = 5
    top_podcast: int = 5


class AppConfig(BaseModel):
    sources: list[SourceConfig] = Field(default_factory=list)
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)


def load_config(path: Path) -> AppConfig:
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return AppConfig.model_validate(raw or {})
