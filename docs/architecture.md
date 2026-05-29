# Architecture

## Purpose

`life-log-sync` is a local-first telemetry sync tool.

It collects personal activity and health data from external services such as Strava and Withings, stores them locally, and generates small context files that can be used by humans or AI assistants.

The project is not a dashboard, not a database server, and not a journal plugin.

## Core Principle

Separate code, telemetry, and narrative.

- Code: `life-log-sync` repository
- Telemetry: application data directory
- Narrative: personal journals

## Data Ownership

### Repository

The repository contains:

- source code
- tests
- documentation
- configuration examples

The repository must not contain:

- OAuth tokens
- raw API responses
- generated CSV files
- generated context files
- personal health or activity data

### Application Data Directory

Runtime data is stored outside the repository.

Default location:

`${XDG_DATA_HOME:-~/.local/share}/life-log-sync`

Example structure:

    life-log-sync/
    ├── strava/
    │   ├── raw/
    │   └── activities.csv
    ├── withings/
    │   ├── raw/
    │   └── body_measures.csv
    └── generated/
        └── today_context.md

This directory contains telemetry and generated files.

It may be deleted and regenerated when possible.

### Personal Journals

Personal journals contain human-written notes only:

- daily notes
- weekly reviews
- reflections
- project notes
- decisions

Personal journals should not be treated as a data lake.

Generated context may be manually copied or summarized into daily notes, but `life-log-sync` should not write raw telemetry into personal journals.

## Current Data Flow

    Strava API
        ↓
    life-log-sync
        ↓
    application data directory
        ↓
    today_context.md
        ↓
    ChatGPT / Codex / manual review

    Withings API
        ↓
    life-log-sync
        ↓
    application data directory
        ↓
    today_context.md

## Generated Context

`today_context.md` is a generated, disposable summary.

Its purpose is to answer questions like:

- What did I do today?
- How active was today?
- Was this a recovery day?
- What should I adjust tomorrow?
- What body measurements were recorded today?

It should be concise and readable.

It is not a permanent journal entry.

## Non-Goals

`life-log-sync` should not:

- become a journal plugin
- write raw telemetry into personal journals
- store secrets in Git
- require a cloud database
- require a web server for normal sync
- overfit to one AI assistant
- become a full productivity system

## Design Rules

- Prefer boring local files.
- Prefer small functions.
- Prefer explicit configuration.
- Keep secrets out of Git.
- Keep generated data out of Git.
- Avoid over-engineering.
- Make the data flow easy to inspect.
- Make manual operation possible before automation.

## Future Integrations

Possible future sources:

- Withings
- Superlist
- Garmin / COROS / Amazfit exports
- Apple Health export
- Sleep tracking

All integrations should follow the same rule:

    External service
        ↓
    life-log-sync
        ↓
    application data directory
        ↓
    generated context

## Relationship with Personal Journals

Personal journals are the narrative layer.

`life-log-sync` may help produce context for writing notes, but it should not own the notes.

A daily note may reference summarized facts such as:

- Walked 4.69 km
- 7,596 steps
- Recovery day

But the raw source data belongs outside personal journals.

## Guiding Sentence

Telemetry is not narrative.
