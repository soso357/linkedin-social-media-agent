#!/usr/bin/env python3
"""Publish a text (+ optional single-image) post to LinkedIn via the REST API.

Setup:
  1. Create an app at https://developer.linkedin.com/, add scopes:
     openid, profile, email, w_member_social
  2. Generate an access token, run:  python3 scripts/linkedin_setup.py
     (prints your LINKEDIN_PERSON_URN)
  3. Put both values in .env (see .env.example)

Usage:
  python3 scripts/publish_linkedin.py --text-file posts/2026-09-26/post.txt
  python3 scripts/publish_linkedin.py --text-file posts/2026-09-26/post.txt --image posts/2026-09-26/visual.png
  python3 scripts/publish_linkedin.py --text "hello" --dry-run   # validate without posting

Image flow: initializeUpload -> PUT binary -> create post referencing urn:li:image.
Docs: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/
"""
import argparse
import json
import os
import sys
import urllib.request

API = "https://api.linkedin.com/rest"


def load_env():
    # minimal .env loader (no dependency)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(root, ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())


def ctx():
    try:
        import certifi
        import ssl
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return None


def req(method, path, token, version, body=None, content_type="application/json", raw=None):
    url = API + path
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Authorization", f"Bearer {token}")
    r.add_header("LinkedIn-Version", version)
    r.add_header("X-Restli-Protocol-Version", "2.0.0")
    if data is not None:
        r.add_header("Content-Type", content_type)
    try:
        with urllib.request.urlopen(r, context=ctx()) as resp:
            payload = resp.read().decode() or "{}"
            headers = {"x-restli-id": resp.headers.get("x-restli-id", "")}
            parsed = json.loads(payload) if payload.strip() else {}
            if isinstance(parsed, dict):
                parsed["_headers"] = headers
            return resp.status, parsed
    except Exception as e:  # urllib.error.HTTPError
        detail = ""
        try:
            detail = e.read().decode()  # type: ignore
        except Exception:
            pass
        print(f"API ERROR {method} {path}: {e}\n{detail}", file=sys.stderr)
        sys.exit(1)


def upload_image(token, version, owner_urn, image_path):
    size = os.path.getsize(image_path)
    status, init = req("POST", "/images?action=initializeUpload", token, version, {
        "initializeUploadRequest": {
            "owner": owner_urn,
        }
    })
    print("initializeUpload:", status, json.dumps(init)[:300])
    value = init.get("value", {})
    upload_url = value.get("uploadUrl")
    image_urn = value.get("image") or value.get("urn")
    if not upload_url or not image_urn:
        print(f"Unexpected initializeUpload response: {init}", file=sys.stderr)
        sys.exit(1)
    with open(image_path, "rb") as f:
        blob = f.read()
    r = urllib.request.Request(upload_url, data=blob, method="PUT")
    r.add_header("Content-Type", "application/octet-stream")
    with urllib.request.urlopen(r, context=ctx()) as resp:
        print("upload bytes:", resp.status)
    return image_urn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text-file")
    ap.add_argument("--text")
    ap.add_argument("--image")
    ap.add_argument("--visibility", default="PUBLIC", choices=["PUBLIC", "CONNECTIONS"])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    load_env()
    token = os.environ.get("LINKEDIN_ACCESS_TOKEN", "")
    owner = os.environ.get("LINKEDIN_PERSON_URN", "")
    version = os.environ.get("LINKEDIN_API_VERSION", "202510")

    if args.text_file:
        with open(args.text_file) as f:
            text = f.read().strip()
    elif args.text:
        text = args.text.strip()
    else:
        print("Provide --text-file or --text", file=sys.stderr)
        sys.exit(2)

    if len(text) > 3000:
        print(f"WARNING: post is {len(text)} chars; LinkedIn limit is 3000. Trim it.", file=sys.stderr)

    image_urn = None
    if args.dry_run or not token or not owner:
        print("--- DRY RUN (no publish) ---" if args.dry_run or True else "")
        print(f"chars: {len(text)}")
        print(f"token: {'set' if token else 'MISSING'} | owner: {owner or 'MISSING'}")
        print(f"image: {args.image or 'none'}")
        if not token or not owner:
            print("Missing credentials — post NOT published. See README setup.", file=sys.stderr)
        print("--- text preview (first 400 chars) ---")
        print(text[:400])
        return

    if args.image:
        image_urn = upload_image(token, version, owner, args.image)

    post = {
        "author": owner,
        "commentary": text,
        "visibility": args.visibility,
        "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [],
                         "thirdPartyDistributionChannels": []},
        "content": {"media": {"id": image_urn, "title": text[:200]}} if image_urn else {},
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }
    status, resp = req("POST", "/posts", token, version, post)
    print("create post:", status, json.dumps(resp)[:500])
    urn = (resp.get("urn") or resp.get("id") or resp.get("value", {}).get("urn", "")
           or resp.get("_headers", {}).get("x-restli-id", ""))
    url_hint = ""
    if urn and ":" in urn:
        post_id = urn.split(":")[-1]
        url_hint = f"https://www.linkedin.com/feed/update/{urn}/"
    print(json.dumps({"post_urn": urn, "url_hint": url_hint}))


if __name__ == "__main__":
    main()
