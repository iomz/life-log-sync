#!/usr/bin/env python3

from __future__ import annotations

import copy
import json
import sys
import tomllib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    import requests
except ImportError as exc:
    raise SystemExit("Missing dependency: run `python3 -m pip install -r requirements.txt`.") from exc

API_URL = "https://www.strava.com/api/v3/athlete/activities"
TOKEN_URL = "https://www.strava.com/oauth/token"
CONFIG_FILE = Path("config.toml")
CONFIG_EXAMPLE_FILE = Path("config.example.toml")
TIMEOUT_SECONDS = 30


def load_config(path: Path = CONFIG_FILE) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(
            f"Missing {path}. Copy {CONFIG_EXAMPLE_FILE} to {path} and fill in your Strava credentials."
        )

    try:
        with path.open("rb") as config_file:
            return tomllib.load(config_file)
    except tomllib.TOMLDecodeError as exc:
        raise SystemExit(f"Could not parse {path}: {exc}") from exc


def write_config(config: dict[str, Any], path: Path = CONFIG_FILE) -> None:
    path.write_text(render_toml(config), encoding="utf-8")


def render_toml(config: dict[str, Any]) -> str:
    lines: list[str] = []
    for section, values in config.items():
        if not isinstance(values, dict):
            continue

        lines.append(f"[{section}]")
        for key, value in values.items():
            lines.append(f"{key} = {format_toml_value(value)}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def format_toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if value is None:
        return '""'
    return json.dumps(str(value))


def require_config_value(section: dict[str, Any], key: str) -> str:
    value = str(section.get(key, "")).strip()
    if not value:
        raise SystemExit(f"Missing strava.{key} in {CONFIG_FILE}.")
    return value


def refresh_access_token(session: requests.Session, config: dict[str, Any]) -> str:
    strava = config.setdefault("strava", {})
    payload = {
        "client_id": require_config_value(strava, "client_id"),
        "client_secret": require_config_value(strava, "client_secret"),
        "grant_type": "refresh_token",
        "refresh_token": require_config_value(strava, "refresh_token"),
    }

    try:
        response = session.post(TOKEN_URL, data=payload, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        token = response.json()
    except requests.HTTPError as exc:
        raise SystemExit(
            f"Strava token refresh failed with HTTP {exc.response.status_code}: {exc.response.text}"
        ) from exc
    except requests.RequestException as exc:
        raise SystemExit(f"Could not reach Strava token endpoint: {exc}") from exc
    except ValueError as exc:
        raise SystemExit("Strava token refresh response was not valid JSON.") from exc

    access_token = token.get("access_token")
    refresh_token = token.get("refresh_token")
    if not access_token or not refresh_token:
        raise SystemExit("Strava token refresh response did not include the expected tokens.")

    strava["access_token"] = access_token
    strava["refresh_token"] = refresh_token
    if "expires_at" in token:
        strava["expires_at"] = token["expires_at"]

    write_config(config)
    return access_token


def get_access_token(session: requests.Session, config: dict[str, Any]) -> str:
    strava = config.get("strava", {})
    if strava.get("refresh_token"):
        return refresh_access_token(session, config)

    access_token = str(strava.get("access_token", "")).strip()
    if access_token:
        return access_token

    raise SystemExit(
        f"Missing Strava credentials. Set strava.refresh_token in {CONFIG_FILE}, "
        "or set strava.access_token for a one-off run."
    )


def fetch_recent_activities(
    session: requests.Session,
    access_token: str,
    *,
    days: int,
    per_page: int,
) -> list[dict[str, Any]]:
    after = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp())
    params = {"after": after, "page": 1, "per_page": per_page}
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        response = session.get(API_URL, headers=headers, params=params, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        activities = response.json()
    except requests.HTTPError as exc:
        body = exc.response.text
        if exc.response.status_code == 401 and "activity:read_permission" in body:
            raise SystemExit(
                "Strava rejected the token: missing activity:read permission. "
                "Re-authorize the app with the activity:read scope."
            ) from exc
        raise SystemExit(
            f"Strava API request failed with HTTP {exc.response.status_code}: {body}"
        ) from exc
    except requests.RequestException as exc:
        raise SystemExit(f"Could not reach Strava API: {exc}") from exc
    except ValueError as exc:
        raise SystemExit("Strava API response was not valid JSON.") from exc

    if not isinstance(activities, list):
        raise SystemExit("Strava API response did not contain a list of activities.")
    return activities


def get_sync_setting(config: dict[str, Any], key: str, default: int) -> int:
    value = config.get("sync", {}).get(key, default)
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise SystemExit(f"sync.{key} must be an integer in {CONFIG_FILE}.") from exc

    if number < 1:
        raise SystemExit(f"sync.{key} must be greater than 0 in {CONFIG_FILE}.")
    return number


def print_activities(activities: list[dict[str, Any]]) -> None:
    for activity in activities:
        name = activity.get("name")
        sport = activity.get("sport_type") or activity.get("type")
        distance_km = activity.get("distance", 0) / 1000
        moving_min = activity.get("moving_time", 0) / 60
        date = activity.get("start_date_local")

        print(f"{date} | {sport} | {distance_km:.2f} km | {moving_min:.0f} min | {name}")


def main() -> int:
    config = load_config()
    config_for_updates = copy.deepcopy(config)
    days = get_sync_setting(config, "days", 7)
    per_page = get_sync_setting(config, "per_page", 10)

    with requests.Session() as session:
        access_token = get_access_token(session, config_for_updates)
        activities = fetch_recent_activities(session, access_token, days=days, per_page=per_page)

    print_activities(activities)
    return 0


if __name__ == "__main__":
    sys.exit(main())
