# life-log-sync

Scripts for syncing personal activity data.

## Strava

`scripts/strava_sync.py` reads recent activities from Strava.

Create `.env.local` with Strava OAuth credentials:

```sh
STRAVA_CLIENT_ID="..."
STRAVA_CLIENT_SECRET="..."
STRAVA_REFRESH_TOKEN="..."
```

The script refreshes `STRAVA_ACCESS_TOKEN` automatically at startup and writes
the latest `STRAVA_ACCESS_TOKEN`, `STRAVA_REFRESH_TOKEN`, and
`STRAVA_EXPIRES_AT` back to `.env.local`.

The authorization must include Strava's `activity:read` scope. A token that can
read `/athlete` is not enough for `/athlete/activities`; Strava returns
`activity:read_permission` as missing when that scope is absent.

For one-off use, you can still provide `STRAVA_ACCESS_TOKEN` in the environment
when refresh credentials are not configured.

Run:

```sh
python3 scripts/strava_sync.py
```
