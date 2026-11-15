#!/bin/sh
# Publishes today's prepared post (local date; override with POST_TZ). Skips if already published or missing.
cd "$(dirname "$0")/.." || exit 1
set -a; . ./.env; set +a
if [ -n "$POST_TZ" ]; then D=$(TZ=$POST_TZ date +%F); else D=$(date +%F); fi
DIR="posts/$D"
[ -f "$DIR/post.txt" ] || { echo "$D: no post"; exit 0; }
grep -q '"status": "published"' "$DIR/meta.json" && { echo "$D: already published"; exit 0; }
OUT=$(/usr/bin/python3 scripts/publish_linkedin.py --text-file "$DIR/post.txt" --image "$DIR/carousel/slide-01.png" 2>&1) || { echo "$D FAILED: $OUT"; exit 1; }
echo "$OUT"
URN=$(echo "$OUT" | sed -n 's/.*"post_urn": "\([^"]*\)".*/\1/p')
/usr/bin/python3 - "$DIR/meta.json" "$URN" <<'P'
import json,sys
p,u=sys.argv[1:];m=json.load(open(p));m["status"]="published";m["linkedin_url"]=f"https://www.linkedin.com/feed/update/{u}/"
json.dump(m,open(p,"w"),indent=1)
P
echo "| $D | published | https://www.linkedin.com/feed/update/$URN/ |" >> content-history.md
