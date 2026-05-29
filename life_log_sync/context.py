from __future__ import annotations

import csv
from collections import Counter
from datetime import date
from pathlib import Path

from life_log_sync.app_data import write_text_file
from life_log_sync.config import AppConfig


def generate_today_context(config: AppConfig, target_date: date | None = None) -> Path:
    target = target_date or date.today()
    activities = activities_for_date(read_strava_activities(config.strava.activities_csv), target)
    measures = measures_for_date(read_withings_measures(config.withings.measures_csv), target)
    content = render_today_context(target, activities, measures)
    return write_text_file(config.today_context_path, content)


def read_strava_activities(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []

    with path.open(encoding="utf-8", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def read_withings_measures(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []

    with path.open(encoding="utf-8", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def activities_for_date(activities: list[dict[str, str]], target_date: date) -> list[dict[str, str]]:
    target = target_date.isoformat()
    return [
        activity
        for activity in activities
        if activity.get("start_date_local", "").startswith(target)
    ]


def measures_for_date(measures: list[dict[str, str]], target_date: date) -> list[dict[str, str]]:
    target = target_date.isoformat()
    return [measure for measure in measures if measure.get("date") == target]


def render_today_context(
    target_date: date,
    activities: list[dict[str, str]],
    measures: list[dict[str, str]] | None = None,
) -> str:
    measures = measures or []
    total_distance_km = sum(_float_value(activity.get("distance_km", "")) for activity in activities)
    total_duration_min = sum(_float_value(activity.get("moving_time_min", "")) for activity in activities)
    activity_types = Counter(activity.get("sport_type") or "Unknown" for activity in activities)

    lines = [
        f"# Today Context - {target_date.isoformat()}",
        "",
        "## Strava",
        "",
    ]

    if not activities:
        lines.append("No Strava activities found for this date.")
        lines.append("")
    else:
        lines.extend(
            [
                f"- Activities: {len(activities)}",
                f"- Distance: {total_distance_km:.2f} km",
                f"- Moving time: {total_duration_min:.0f} min",
                f"- Types: {_format_activity_types(activity_types)}",
                "",
                "### Activities",
                "",
            ]
        )

        for activity in activities:
            lines.append(
                "- "
                f"{activity.get('sport_type') or 'Unknown'}: "
                f"{activity.get('name') or 'Untitled'} "
                f"({activity.get('distance_km') or '0.00'} km, "
                f"{_format_minutes(activity.get('moving_time_min', ''))})"
            )
        lines.append("")

    lines.extend(["## Withings", ""])

    if not measures:
        lines.append("No Withings body measurements found for this date.")
        lines.append("")
        return "\n".join(lines)

    for measure in measures:
        lines.append(
            "- "
            f"{measure.get('type_name') or 'measurement'}: "
            f"{measure.get('value') or '0.00'} {measure.get('unit') or ''}".rstrip()
        )

    lines.append("")
    return "\n".join(lines)


def _format_activity_types(activity_types: Counter[str]) -> str:
    return ", ".join(
        f"{activity_type} x{count}" if count > 1 else activity_type
        for activity_type, count in sorted(activity_types.items())
    )


def _format_minutes(value: str) -> str:
    return f"{_float_value(value):.0f} min"


def _float_value(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
