---
description: Run the daily LinkedIn workflow — research, write, visual, QC, publish, record.
agent: linkedin-marketer
---

Run today's full Daily LinkedIn Marketing Content Agent workflow for date $ARGUMENTS (default: today, UTC).

Follow the linkedin-marketer agent instructions exactly: Research → Filter → Select Topic → Develop Insight → Write Post → Create Visual → Quality Check → Publish → Record.

Working directory is the project root (where opencode.jsonc lives). Read content-history.json first to avoid repetition. Save everything under posts/<YYYY-MM-DD>/ and update both history files. If LinkedIn credentials are missing, leave the post ready and report the blocker clearly.
