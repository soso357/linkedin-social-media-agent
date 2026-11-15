#!/usr/bin/env python3
"""Exchange nothing — just resolve and print your LinkedIn person URN.

Usage:
  LINKEDIN_ACCESS_TOKEN=xxx python3 scripts/linkedin_setup.py
Reads .env automatically. Calls GET /v2/userinfo (OpenID) and prints
urn:li:person:{sub} to put in .env as LINKEDIN_PERSON_URN.
"""
import json
import os
import urllib.request

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(root, ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

token = os.environ.get("LINKEDIN_ACCESS_TOKEN", "")
if not token:
    print("Set LINKEDIN_ACCESS_TOKEN first (see README).")
    raise SystemExit(2)

try:
    import certifi
    import ssl
    ctx = ssl.create_default_context(cafile=certifi.where())
except Exception:
    ctx = None

r = urllib.request.Request("https://api.linkedin.com/v2/userinfo")
r.add_header("Authorization", f"Bearer {token}")
with urllib.request.urlopen(r, context=ctx) as resp:
    data = json.loads(resp.read().decode())
print(json.dumps(data, indent=2)[:800])
sub = data.get("sub")
if sub:
    print(f"\nLINKEDIN_PERSON_URN=urn:li:person:{sub}")
