#!/usr/bin/env python3

import os
import json
from datetime import datetime, timedelta, timezone
from urllib import error, parse, request

API_URL = "https://www.strava.com/api/v3/athlete/activities"
TOKEN_URL = "https://www.strava.com/oauth/token"
ENV_FILE = ".env.local"


def parse_env_value(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def load_env_file(path=ENV_FILE):
    if not os.path.exists(path):
        return {}

    values = {}
    with open(path, encoding="utf-8") as env_file:
        for line in env_file:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue

            key, value = stripped.split("=", 1)
            key = key.strip()
            if key:
                values[key] = parse_env_value(value)
                os.environ.setdefault(key, values[key])

    return values


def require_env(name):
    try:
        return os.environ[name]
    except KeyError as exc:
        raise SystemExit(f"Missing {name} in the environment or {ENV_FILE}.") from exc


def update_env_file(updates, path=ENV_FILE):
    lines = []
    seen = set()

    if os.path.exists(path):
        with open(path, encoding="utf-8") as env_file:
            lines = env_file.readlines()

    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue

        key = stripped.split("=", 1)[0].strip()
        if key in updates:
            lines[index] = f"{key}={updates[key]}\n"
            seen.add(key)

    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"

    for key, value in updates.items():
        if key not in seen:
            lines.append(f"{key}={value}\n")

    with open(path, "w", encoding="utf-8") as env_file:
        env_file.writelines(lines)


def refresh_access_token():
    data = parse.urlencode(
        {
            "client_id": require_env("STRAVA_CLIENT_ID"),
            "client_secret": require_env("STRAVA_CLIENT_SECRET"),
            "grant_type": "refresh_token",
            "refresh_token": require_env("STRAVA_REFRESH_TOKEN"),
        }
    ).encode("utf-8")
    req = request.Request(TOKEN_URL, data=data, method="POST")

    try:
        with request.urlopen(req, timeout=30) as res:
            token = json.loads(res.read())
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Strava token refresh failed with HTTP {exc.code}: {body}") from exc
    except error.URLError as exc:
        raise SystemExit(f"Could not reach Strava token endpoint: {exc.reason}") from exc

    access_token = token.get("access_token")
    refresh_token = token.get("refresh_token")
    if not access_token or not refresh_token:
        raise SystemExit("Strava token refresh response did not include the expected tokens.")

    updates = {
        "STRAVA_ACCESS_TOKEN": access_token,
        "STRAVA_REFRESH_TOKEN": refresh_token,
    }
    if "expires_at" in token:
        updates["STRAVA_EXPIRES_AT"] = str(token["expires_at"])

    update_env_file(updates)
    os.environ.update(updates)
    return access_token


def get_access_token():
    load_env_file()
    refresh_configured = all(
        os.environ.get(name)
        for name in ("STRAVA_CLIENT_ID", "STRAVA_CLIENT_SECRET", "STRAVA_REFRESH_TOKEN")
    )
    if refresh_configured:
        return refresh_access_token()

    try:
        return os.environ["STRAVA_ACCESS_TOKEN"]
    except KeyError as exc:
        raise SystemExit(
            "Missing Strava credentials. Set STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, "
            f"and STRAVA_REFRESH_TOKEN in {ENV_FILE}, or provide STRAVA_ACCESS_TOKEN."
        ) from exc


def fetch_recent_activities(access_token):
    after = int((datetime.now(timezone.utc) - timedelta(days=7)).timestamp())
    url = f"{API_URL}?{parse.urlencode({'after': after, 'page': 1, 'per_page': 10})}"
    req = request.Request(url, headers={"Authorization": f"Bearer {access_token}"})

    try:
        with request.urlopen(req, timeout=30) as res:
            return res.read()
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        if exc.code == 401 and "activity:read_permission" in body:
            raise SystemExit(
                "Strava rejected the token: missing activity:read permission. "
                "Re-authorize the app with the activity:read scope and export the new access token."
            ) from exc
        raise SystemExit(f"Strava API request failed with HTTP {exc.code}: {body}") from exc
    except error.URLError as exc:
        raise SystemExit(f"Could not reach Strava API: {exc.reason}") from exc


ACCESS_TOKEN = get_access_token()
activities = json.loads(fetch_recent_activities(ACCESS_TOKEN))

for a in activities:
    name = a.get("name")
    sport = a.get("sport_type") or a.get("type")
    distance_km = a.get("distance", 0) / 1000
    moving_min = a.get("moving_time", 0) / 60
    date = a.get("start_date_local")

    print(f"{date} | {sport} | {distance_km:.2f} km | {moving_min:.0f} min | {name}")
