# Tesla AI

Tesla AI is a Home Assistant custom integration and dashboard package for Tesla-focused trip, charge, Live Trip and AI-assisted reporting.

> This project is not affiliated with, endorsed by, or sponsored by Tesla, Inc.

## What it does

- Tesla-style Home Assistant dashboard
- Drive dashboard for Tesla browser use
- Live Trip tracking and Live Trip AI comments
- Trip and charge visual reports
- Built-in Telegram bot support
- Optional OpenAI-powered driving comments and summaries
- Trip Records and Charge Records
- Entity mapping / Auto Find tools
- Debug and support report tools

## Important

The technical Home Assistant integration domain is still:

```text
pom_tesla_report
```

Do not rename the folder or domain unless you also migrate all Home Assistant config entries, entities, resources and generated dashboard references.

The visible app name is now **Tesla AI**.

## Installation

Copy the integration folder into Home Assistant:

```text
custom_components/pom_tesla_report
```

Then restart Home Assistant.

After installation:

1. Open **Tesla AI** from the Home Assistant sidebar.
2. Configure language, currency, entities, Telegram and AI settings.
3. Run dashboard rebuild from the panel.
4. Hard-refresh the browser.

## Secrets and API keys

Do not commit Home Assistant runtime config, `.storage` files, support reports, backups or exported settings that may contain real API keys or Telegram bot tokens.

This repository should not contain any real OpenAI API key, Telegram token or private Home Assistant configuration.

## Notes

- Built-in Telegram bot support is included; Home Assistant's Telegram integration is not required for the built-in bot flow.
- OpenAI API key is optional and should be entered from the UI.
- Reverse geocoding address cache is internally fixed at 60 minutes in the current UI.
