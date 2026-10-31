#!/usr/bin/env python3
"""Quote the content-use terms of each bureau's own page (saved under evidence/terms/) into docs/bureau_terms.json,
and set docs/licence_status.json: a bureau is confirmed when its own terms name the Public Data License 1.0.

    uv run python scripts/00_terms.py
"""

import hashlib
import html
import json
import re
import subprocess

import kansui
import terms

ROOT = kansui.root()
PAGES = {  # bureau: (file in evidence/terms, URL it was fetched from)
    "thr": ("thr_policy.pdf", "https://www.thr.mlit.go.jp/policy.pdf"),
    "ktr": ("ktr_copyright.html", "https://www.ktr.mlit.go.jp/guide/copyright.html"),
    "hrr": ("hrr_help.html", "https://www.hrr.mlit.go.jp/help.html"),
    "cbr": ("cbr_policy.html", "https://www.cbr.mlit.go.jp/policy.htm"),
    "kkr": ("kkr_link.html", "https://www.kkr.mlit.go.jp/link.html"),
    "skr": ("skr_manual.html", "https://www.skr.mlit.go.jp/manual.html"),
    "qsr": ("qsr_pp.html", "https://www.qsr.mlit.go.jp/pp/index.html"),
    "cgr": ("cgr_manual.html", "https://www.cgr.mlit.go.jp/about_manual/index.html"),
}


def page_text(p) -> str:
    if p.suffix == ".pdf":
        t = subprocess.run(
            ["pdftotext", "-layout", str(p), "-"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    else:
        s = p.read_text(encoding="utf-8", errors="replace")
        t = re.sub(r"<script.*?</script>|<style.*?</style>", "", s, flags=re.DOTALL)
        t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    return re.sub(r"\s+", " ", t)


def main() -> int:
    out, status = {}, {}
    for b, (f, url) in PAGES.items():
        p = ROOT / "evidence" / "terms" / f
        r = terms.extract_terms(page_text(p))
        ok = "公共データ利用規約" in r["use_sentence"] and (
            "PDL1.0" in r["use_sentence"] or "1.0" in r["use_sentence"].replace(" ", "")
        )
        out[b] = {
            "url": url,
            "file": f,
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            **r,
        }
        status[b] = {"confirmed": ok, "url": url,
                     "basis": "the bureau's own site terms (link, copyright and policy page) name the Public Data License 1.0"}  # fmt: skip
    (ROOT / "docs" / "bureau_terms.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n"
    )
    (ROOT / "docs" / "licence_status.json").write_text(
        json.dumps(
            {
                "scope": "site-wide terms of each bureau. No data-specific licence notice exists on the Webmap pages or in the KML (checked 2026-10-30).",
                "bureaus": status,
            },
            ensure_ascii=False,
            indent=1,
        )
        + "\n"
    )
    for b, v in out.items():
        print(
            b,
            status[b]["confirmed"],
            "|",
            v["use_sentence"][:110],
            "| important:",
            (v["important"] or "")[:40],
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
