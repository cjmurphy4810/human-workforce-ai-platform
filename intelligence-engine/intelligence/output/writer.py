"""Output Writer — serialises an IntelligenceReport to JSON and Markdown files.

Five output files are written to a dated subdirectory:
  executive_intelligence.json
  executive_intelligence.md
  executive_recommendations.json
  trend_analysis.json
  consulting_pipeline.json
"""

from __future__ import annotations

import dataclasses
import json
import logging
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from intelligence.models.intelligence import (
    IntelligenceReport,
    OpportunityType,
    Priority,
    TrendType,
)

logger = logging.getLogger(__name__)

# ── JSON serialisation ────────────────────────────────────────────────────────


class _EnumAwareEncoder(json.JSONEncoder):
    def default(self, obj: object) -> object:
        if isinstance(obj, datetime):
            return obj.isoformat()
        if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
            return dataclasses.asdict(obj)  # type: ignore[call-overload]
        return super().default(obj)


def _dump(obj: object) -> str:
    return json.dumps(obj, cls=_EnumAwareEncoder, indent=2, ensure_ascii=False)


def _report_to_dict(report: IntelligenceReport) -> dict:  # type: ignore[type-arg]
    d = asdict(report)  # type: ignore[call-overload]
    d["generated_at"] = report.generated_at.isoformat()
    return d


# ── Markdown generation ───────────────────────────────────────────────────────


def _md_priority_emoji(p: Priority) -> str:
    return {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(p.value, "⚪")


def _md_trend_label(t: str) -> str:
    return {
        TrendType.EMERGING.value: "🚀 Emerging",
        TrendType.GROWING.value: "📈 Growing",
        TrendType.DECLINING.value: "📉 Declining",
        TrendType.REPEATED.value: "🔄 Repeated",
        TrendType.INDUSTRY_PATTERN.value: "🏭 Industry Pattern",
        TrendType.VENDOR_ACTIVITY.value: "🏢 Vendor Activity",
        TrendType.ENTERPRISE_RISK.value: "⚠️ Enterprise Risk",
    }.get(t, t)


def _generate_markdown(report: IntelligenceReport) -> str:
    s = report.summary
    lines: list[str] = [
        "# Executive Intelligence Report",
        "",
        f"**Generated:** {report.generated_at.strftime('%Y-%m-%d %H:%M UTC')}  ",
        f"**Analysis Period:** {report.period_days} days  ",
        f"**Articles Analyzed:** {s.total_articles_analyzed:,}",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Opportunities Detected | {s.opportunities_detected} |",
        f"| High Priority | {s.high_priority_opportunities} |",
        f"| Medium Priority | {s.medium_priority_opportunities} |",
        f"| Trends Identified | {s.trends_identified} |",
        f"| Emerging Trends | {s.emerging_trends} |",
        f"| Executive Actions Required | {s.executive_actions_required} |",
        f"| Top Consulting Value | {s.top_consulting_value} |",
        "",
    ]

    # Opportunities
    if report.opportunities:
        lines += ["## Opportunities", ""]
        for opp in report.opportunities:
            emoji = _md_priority_emoji(opp.priority)
            lines += [
                f"### {emoji} {opp.title} `[{opp.type.value.replace('_', ' ').title()}]`",
                "",
                f"- **Priority:** {opp.priority.value.title()}",
                f"- **Confidence:** {opp.confidence:.0%}",
                f"- **Business Value:** {opp.estimated_business_value}",
                f"- **Target Audience:** {opp.target_audience}",
                f"- **Action:** {opp.recommended_action}",
                "",
                f"**Supporting Articles ({len(opp.supporting_articles)}):**",
            ]
            for ref in opp.supporting_articles[:3]:
                lines.append(f"- [{ref.title}]({ref.url}) — {ref.source} (score: {ref.overall_score:.2f})")
            lines.append("")

    # Trends
    if report.trends:
        lines += ["## Trend Analysis", ""]
        for trend in report.trends:
            lines += [
                f"### {_md_trend_label(trend.type.value)}: {trend.topic}",
                "",
                f"- **Velocity:** {trend.velocity:+.2f}",
                f"- **Recent Articles:** {trend.recent_count} | **Baseline:** {trend.baseline_count}",
                f"- **Average Score:** {trend.avg_score:.2f}",
                f"- **Sources:** {', '.join(trend.key_sources[:3])}",
                "",
            ]
            for title in trend.sample_titles[:2]:
                lines.append(f"> _{title}_")
            lines.append("")

    # Impact Analysis
    if report.impact_analysis:
        lines += ["## Executive Impact Analysis", ""]
        lines += [
            "| Topic | Articles | Business | Technology | Op.Risk | Gov | Regulatory | Fin.Svc | Exec Priority | Time Sens. |",
            "|-------|----------|----------|-----------|---------|-----|-----------|---------|--------------|-----------|",
        ]
        for imp in report.impact_analysis:
            lines.append(
                f"| {imp.topic} | {imp.article_count} "
                f"| {imp.business_impact:.2f} | {imp.technology_impact:.2f} "
                f"| {imp.operational_risk:.2f} | {imp.governance_impact:.2f} "
                f"| {imp.regulatory_impact:.2f} | {imp.financial_services_relevance:.2f} "
                f"| {imp.executive_priority:.2f} | {imp.time_sensitivity:.2f} |"
            )
        lines.append("")

    # Recommendations
    if report.recommendations:
        lines += ["## Recommendations", ""]
        action_sections: dict[str, list[str]] = {}
        for rec in report.recommendations:
            section = rec.action.value.replace("_", " ").title()
            action_sections.setdefault(section, [])
            action_sections[section].append(
                f"- **{rec.title}** (score: {rec.score:.2f})  \n  _{rec.reasoning}_"
            )
        for section, items in action_sections.items():
            lines += [f"### {section}", ""] + items[:10] + [""]

    return "\n".join(lines)


# ── Writer ────────────────────────────────────────────────────────────────────


def write_outputs(report: IntelligenceReport, output_dir: Path) -> dict[str, Path]:
    """Write all five output files and return a mapping of filename → path."""
    dated_dir = output_dir / report.generated_at.strftime("%Y-%m-%d")
    dated_dir.mkdir(parents=True, exist_ok=True)

    written: dict[str, Path] = {}

    # ── executive_intelligence.json ───────────────────────────────────────────
    report_dict = _report_to_dict(report)
    p = dated_dir / "executive_intelligence.json"
    p.write_text(_dump(report_dict), encoding="utf-8")
    written["executive_intelligence.json"] = p

    # ── executive_intelligence.md ─────────────────────────────────────────────
    p = dated_dir / "executive_intelligence.md"
    p.write_text(_generate_markdown(report), encoding="utf-8")
    written["executive_intelligence.md"] = p

    # ── executive_recommendations.json ────────────────────────────────────────
    recs_payload = {
        "generated_at": report.generated_at.isoformat(),
        "total": len(report.recommendations),
        "recommendations": [asdict(r) for r in report.recommendations],  # type: ignore[call-overload]
    }
    p = dated_dir / "executive_recommendations.json"
    p.write_text(_dump(recs_payload), encoding="utf-8")
    written["executive_recommendations.json"] = p

    # ── trend_analysis.json ───────────────────────────────────────────────────
    trends_by_type: dict[str, list[dict]] = {t.value: [] for t in TrendType}  # type: ignore[type-arg]
    for trend in report.trends:
        trends_by_type[trend.type.value].append(asdict(trend))  # type: ignore[call-overload]
    trend_payload = {
        "generated_at": report.generated_at.isoformat(),
        "analysis_window_days": report.period_days,
        "recent_window_days": 7,
        "total_trends": len(report.trends),
        "trends": trends_by_type,
    }
    p = dated_dir / "trend_analysis.json"
    p.write_text(_dump(trend_payload), encoding="utf-8")
    written["trend_analysis.json"] = p

    # ── consulting_pipeline.json ──────────────────────────────────────────────
    consulting = [asdict(o) for o in report.opportunities if o.type == OpportunityType.CONSULTING]  # type: ignore[call-overload]
    pipeline_payload = {
        "generated_at": report.generated_at.isoformat(),
        "total": len(consulting),
        "pipeline": consulting,
    }
    p = dated_dir / "consulting_pipeline.json"
    p.write_text(_dump(pipeline_payload), encoding="utf-8")
    written["consulting_pipeline.json"] = p

    logger.info("intelligence outputs written to %s", dated_dir)
    return written
