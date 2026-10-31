#!/usr/bin/env python3
"""Fetch the unique 箇所表 PDFs linked from the KML, politely, with sha256 and Last-Modified (resumable).

    uv run python -u scripts/07_fetch_pdfs.py      # data/raw/<date>/pdf/*.pdf and PDF_MANIFEST.json

One request at a time, 2 s pause, one retry after 60 s. A 404 is recorded and the run goes on; the run stops on a 403/429 or
on 5 failed URLs in a row. The PDFs are kept locally only: they are not uploaded (their sha256 is).
"""

import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import geopandas as gpd
import kansui

ROOT = kansui.root()


def fetch(url: str):
    req = urllib.request.Request(urllib.parse.quote(url, safe=":/?&=%#~+,;@!*()'$[]"), headers={"User-Agent": kansui.UA})
    for attempt in (0, 1):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.status, r.read(), {k.lower(): v for k, v in r.headers.items()}
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                raise SystemExit(f"blocked: HTTP {e.code} for {url}") from e
            if e.code == 404:
                return 404, b"", {}
            if attempt:
                return e.code, b"", {}
        except (urllib.error.URLError, TimeoutError):
            if attempt:
                return 0, b"", {}
        time.sleep(60)
    return 0, b"", {}


def main() -> int:
    run = max((ROOT / "data" / "raw").glob("*/MANIFEST.json")).parent
    out = run / "pdf"
    out.mkdir(exist_ok=True)
    mp = run / "PDF_MANIFEST.json"
    man = json.loads(mp.read_text()) if mp.exists() else {"files": {}}
    pts = gpd.read_parquet(ROOT / "data" / "parquet" / "kansui_points.parquet")
    plan = kansui.pdf_plan(pts["pdf_url"])
    print(len(plan), "unique PDFs;", len(man["files"]), "already done", flush=True)
    bad_in_row, t0 = 0, time.time()
    for i, url in enumerate(plan, 1):
        name = kansui.pdf_name(url)
        if name in man["files"] and man["files"][name]["status"] in (200, 404):
            continue
        code, body, h = fetch(url)
        rec = {"url": url, "status": code, "size": len(body)}
        if code == 200:
            (out / name).write_bytes(body)
            rec |= {
                "sha256": hashlib.sha256(body).hexdigest(),
                "last_modified": h.get("last-modified"),
                "content_type": h.get("content-type"),
            }
            bad_in_row = 0
        elif code != 404:
            bad_in_row += 1
        man["files"][name] = rec
        if i % 25 == 0:
            mp.write_text(json.dumps(man, ensure_ascii=False, indent=1))
            print(f"{i}/{len(plan)} {time.time() - t0:.0f}s last {code}", flush=True)
        if bad_in_row >= 5:
            mp.write_text(json.dumps(man, ensure_ascii=False, indent=1))
            raise SystemExit("5 failures in a row: stop")
        time.sleep(kansui.PAUSE_S)
    man["fetched_all"] = True
    mp.write_text(json.dumps(man, ensure_ascii=False, indent=1))
    print(
        "done",
        len(man["files"]),
        "records;",
        sum(1 for v in man["files"].values() if v["status"] == 404),
        "missing (404)",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
