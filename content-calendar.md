# Content Calendar

Visuals: one 1080x1080 image. Dark velvet-blue background, ONLY the hook (first paragraph of post.txt) in white bold, your name (`AUTHOR_NAME` in `.env`) bottom-left. Render:
`python3 scripts/render_hook.py --post-file posts/<DATE>/post.txt --out posts/<DATE>/carousel/slide-01.png`
(publish_today.sh publishes carousel/slide-01.png). Keep hooks to ~12 words max.
Every post gets differently shaped waves (seeded from the hook). If one looks like a recent post, re-render with `--seed <any new number>`.

Every topic is a direction. Research fresh (last 7 days) evidence on the day, as the agent rules require.

| Date | Day | Pillar | Topic | Angle | Source | Status |
|---|---|---|---|---|---|---|
| 2026-01-05 | Mon | Performance | Incrementality testing | Which sales would have happened anyway? One simple holdout test. | new | todo |
| 2026-01-06 | Tue | AI in marketing | Brand voice guardrails for AI | A one-page voice guide that stops AI copy from sounding like everyone else. | new | todo |
| 2026-01-07 | Wed | Growth | Email list as owned channel | The list you own is the cheapest reach you have. | new | todo |
