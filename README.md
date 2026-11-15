# LinkedIn Social Media Content Agent

An autonomous AI agent that runs your daily LinkedIn content:
**Research → Filter → Select → Write → Visual → QC → Publish → Record.**

It finds fresh marketing/AI news (last 7 days), writes an operator-style post (max 200 words, no AI-sounding filler), renders a 1080x1080 visual with your hook and name, quality-checks it, publishes through the official LinkedIn API and logs history so topics never repeat.

Built for [opencode](https://opencode.ai). The agent prompt lives in `.opencode/agents/linkedin-marketer.md` and works with any coding agent (Claude Code, etc.) if you point it at that file.

## Setup

```sh
git clone <this repo> && cd linkedin-content-agent
pip install pillow                   # visuals (API uses stdlib only)
cp .env.example .env                 # fill in values below
```

1. Create an app at https://developer.linkedin.com/ with products **Share on LinkedIn** + **Sign In with LinkedIn using OpenID Connect**.
2. Scopes: `openid profile email w_member_social` → generate an access token (lasts ~60 days).
3. Get your person URN:
   ```sh
   LINKEDIN_ACCESS_TOKEN=xxx python3 scripts/linkedin_setup.py
   ```
4. Put `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_PERSON_URN` and `AUTHOR_NAME` in `.env`.
5. Optional: add your photo as `assets/profile.png`.
6. Test without posting:
   ```sh
   python3 scripts/publish_linkedin.py --text "hello" --dry-run
   ```

## Daily use

```sh
opencode "/linkedin-daily"       # research, write, render, QC, publish
./scripts/publish_today.sh       # publish today's already-prepared post
```

Plan topics in `content-calendar.md` – the agent uses today's row as the starting direction.

### Auto-publish every morning (macOS / Linux cron)

```sh
crontab -e
# 08:30 daily:
30 8 * * * /path/to/linkedin-content-agent/scripts/publish_today.sh >> /path/to/linkedin-content-agent/logs/publish.log 2>&1
```

Set `POST_TZ` (e.g. `Europe/London`) in `.env` if your posting date should follow a specific timezone.

## Layout

```text
.opencode/agents/linkedin-marketer.md   # the agent (system prompt)
.opencode/commands/linkedin-daily.md    # /linkedin-daily command
scripts/publish_linkedin.py             # LinkedIn REST API publisher (text + image)
scripts/publish_today.sh                # publishes today's post, updates history
scripts/render_hook.py                  # hook-only velvet visual with your name
scripts/render_carousel.py              # multi-slide carousel + PDF
scripts/generate_visual_ai.py           # free AI background + text overlay
scripts/render_visual.py                # coded SVG/PNG card fallback
scripts/linkedin_setup.py               # resolves your person URN
content-calendar.md                     # topic plan
content-history.json / .md              # dedup + performance log
posts/YYYY-MM-DD/                       # research.md, post.txt, visual, meta.json
```

## Notes

- `render_hook.py` uses macOS Helvetica Neue; on Linux/Windows change `FONT` in the script to a local .ttf.
- LinkedIn API version header defaults to `202501` (override with `LINKEDIN_API_VERSION`).
- Tokens expire every ~60 days – regenerate and update `.env`.
- Never commit `.env`.
