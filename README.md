# life-log-sync

Scripts for syncing personal activity data.

## Strava

`scripts/strava_sync.py` reads recent activities from Strava.

Install dependencies:

```sh
python3 -m pip install -r requirements.txt
```

Create `config.toml` from the example and add your Strava OAuth credentials:

```sh
cp config.example.toml config.toml
```

Never commit `config.toml`. It contains OAuth credentials and refreshed tokens
that can access your Strava data. The repository ignores this file by default.

The script refreshes the Strava access token automatically at startup and
writes the latest `access_token`, `refresh_token`, and `expires_at` back to
`config.toml`.

The authorization must include Strava's `activity:read` scope. A token that can
read `/athlete` is not enough for `/athlete/activities`; Strava returns
`activity:read_permission` as missing when that scope is absent.

For one-off use, you can set `strava.access_token` in `config.toml` when
refresh credentials are not configured.

Run:

```sh
python3 scripts/strava_sync.py
```
