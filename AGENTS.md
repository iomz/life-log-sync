# AGENTS.md

## Project Purpose

life-log-sync synchronizes personal telemetry data
from Strava, Withings, and other sources.

The repository contains code only.

## Architecture

Code:

- repository

Telemetry:

- ${XDG_DATA_HOME}/life-log-sync

Narrative:

- Personal Journals

## Rules

- Never store personal data in the repository.
- Prefer small functions.
- Avoid over-engineering.
