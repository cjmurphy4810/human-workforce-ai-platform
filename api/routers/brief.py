from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_agent1_dir, get_config
from api.models.responses import BriefResponse

router = APIRouter(tags=["Brief"])


@router.get(
    "/brief/latest",
    response_model=BriefResponse,
    summary="Latest Executive Brief",
    description=(
        "Returns the most recently generated Executive Brief as Markdown. "
        "Run `POST /run` first if no brief exists."
    ),
)
async def get_latest_brief(
    config=Depends(get_config),
    agent1_dir: Path = Depends(get_agent1_dir),
) -> BriefResponse:
    output_root = agent1_dir / config.output.directory
    brief_path, date_str = _find_latest_brief(output_root)

    if brief_path is None:
        raise HTTPException(
            status_code=404,
            detail="No brief found. Run POST /run to generate one.",
        )

    content = brief_path.read_text(encoding="utf-8")
    return BriefResponse(
        date=date_str,
        path=str(brief_path),
        content=content,
        word_count=len(content.split()),
        character_count=len(content),
    )


def _find_latest_brief(output_root: Path) -> tuple[Path | None, str]:
    if not output_root.exists():
        return None, ""

    candidates = sorted(output_root.glob("????-??-??"), reverse=True)

    for date_dir in candidates:
        brief = date_dir / "executive_brief.md"
        if brief.exists():
            return brief, date_dir.name

    return None, ""
