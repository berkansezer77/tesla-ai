# POM Tesla Report v2.1.1-beta.1

Initial public beta.

## Highlights

- AI-powered Telegram assistant for Tesla/Home Assistant workflows
- Prefix-free Telegram AI listener
- Curated capability router for vehicle controls
- Button and text-based confirmation flow
- Manual entity selection for report and AI context
- Trip reports, charging reports, and optional map images
- Separate map PNG sending can be enabled or disabled from settings
- Conversation memory limited to the latest turn to reduce stale AI behavior
- New installs ship with empty/default-free entity configuration

## Safety

This beta can send real vehicle commands. Configure entities carefully and test with low-risk commands first.

## Recommended First Tests

1. Ask a read-only status question.
2. Generate a test trip report.
3. Enable Telegram AI and ask a simple question.
4. Test a safe command.
5. Test a confirmation-required command.

## Known Beta Notes

- Home Assistant integration icon may show as unavailable until a Home Assistant Brands entry is added.
- Users must manually select their own entities; no personal entity IDs are included.
