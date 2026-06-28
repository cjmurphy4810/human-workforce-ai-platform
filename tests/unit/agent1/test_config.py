from __future__ import annotations

from pathlib import Path

import pytest
from config.loader import ScoringWeights, load_config
from pydantic import ValidationError

_CONFIG_YAML = (
    Path(__file__).parent.parent.parent.parent / "agent1-research" / "config" / "config.yaml"
)


def test_load_bundled_config() -> None:
    cfg = load_config(_CONFIG_YAML)
    assert len(cfg.sources) > 0
    assert cfg.output.top_stories > 0


def test_default_weights_sum_to_one() -> None:
    w = ScoringWeights()
    total = (
        w.business_impact
        + w.executive_interest
        + w.consulting_opportunity
        + w.podcast_potential
        + w.urgency
    )
    assert abs(total - 1.0) < 0.001


def test_invalid_weights_raise() -> None:
    with pytest.raises(ValidationError):
        ScoringWeights(
            business_impact=0.50,
            executive_interest=0.50,
            consulting_opportunity=0.50,
            podcast_potential=0.50,
            urgency=0.50,
        )


def test_missing_config_raises() -> None:
    with pytest.raises(FileNotFoundError):
        load_config(Path("/does/not/exist.yaml"))


def test_source_count() -> None:
    cfg = load_config(_CONFIG_YAML)
    names = {s.name for s in cfg.sources}
    assert len(names) == len(cfg.sources), "duplicate source names"


def test_default_config_from_empty_yaml(tmp_path: Path) -> None:
    empty = tmp_path / "empty.yaml"
    empty.write_text("{}")
    cfg = load_config(empty)
    assert cfg.sources == []
    assert cfg.output.lookback_days == 7
