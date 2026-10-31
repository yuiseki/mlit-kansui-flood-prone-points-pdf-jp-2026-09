#!/usr/bin/env python3
"""Download the 45 KML files (the 40 of the user's list plus the 5 of the Chugoku bureau) of 冠水想定箇所 from the bureaus' web maps, politely, with sha256 and Last-Modified.

    uv run python scripts/01_collect.py     # writes data/raw/<date>/kml/*.kml, MANIFEST.json

One request at a time, a pause between requests, no retries beyond one after 60 s.
"""

import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import date

import kansui

ROOT = kansui.root()


def fetch(url: str) -> tuple[bytes, dict]:
    req = urllib.request.Request(url, headers={"User-Agent": kansui.UA})
    for attempt in (0, 1):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read(), {k.lower(): v for k, v in r.headers.items()}
        except urllib.error.URLError as e:
            if attempt:
                raise
            print(f"retry after 60 s: {url}: {e}", file=sys.stderr)
            time.sleep(60)
    raise AssertionError


def main() -> int:
    bases = kansui.parse_bases(
        (ROOT / "data" / "bases_from_user.txt").read_text()
        + (ROOT / "data" / "bases_added.txt").read_text()
    )
    out = ROOT / "data" / "raw" / date.today().strftime("%Y%m%d")
    (out / "kml").mkdir(parents=True, exist_ok=True)
    man = {"fetched": date.today().isoformat(), "files": {}}
    for layer, base in bases.items():
        url = kansui.kml_url(base, layer)
        body, h = fetch(url)
        (out / "kml" / f"{layer}.kml").write_bytes(body)
        man["files"][layer] = {
            "url": url, "size": len(body), "sha256": hashlib.sha256(body).hexdigest(),
            "last_modified": h.get("last-modified"), "content_type": h.get("content-type"),
            "bureau": kansui.bureau_of(base),
        }  # fmt: skip
        print(layer, len(body), h.get("last-modified"))
        time.sleep(kansui.PAUSE_S)
    (out / "MANIFEST.json").write_text(json.dumps(man, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
