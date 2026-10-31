#!/usr/bin/env python3
"""Parse the tables of the fetched 箇所表 PDFs into one row per described point (as published; null where unreadable).

    uv run python -u scripts/08_parse_pdfs.py     # data/parquet/pdf_records_as_read.parquet, docs/pdf_parse_log.json

Layouts: A (説明表 / 箇所表 / 様式), B (道路冠水(危険)想定箇所 forms). Anything else gets one row with layout 'unknown' and
parse_status 'layout_unknown'. A row whose required cells are not all read gets 'ambiguous'. Nothing is guessed.
"""

import collections
import json
import sys
import warnings

import kansui
import pandas as pd
import pdfparse
import pdfplumber

ROOT = kansui.root()
COLS = ["mgmt_no", "place_name", "road_name", "underpass_name", "road_kind", "pref_name", "municipality", "aza_chome",
        "banchi", "sakimei", "manager_name", "manager_tel", "manager_tel_text", "police_name", "police_tel", "police_text",
        "fire_name", "fire_tel", "fire_text", "remarks", "extra_cells", "parse_note"]  # fmt: skip


def main() -> int:
    warnings.filterwarnings("ignore")
    run = max((ROOT / "data" / "raw").glob("*/MANIFEST.json")).parent
    man = json.loads((run / "PDF_MANIFEST.json").read_text())["files"]
    rows, stat, errors = [], collections.Counter(), []
    for n, (name, m) in enumerate(sorted(man.items()), 1):
        if m["status"] != 200:
            continue
        try:
            with pdfplumber.open(run / "pdf" / name) as p:
                pages = len(p.pages)
                tables = [t for pg in p.pages for t in pg.extract_tables()]
            layout, recs = pdfparse.parse_tables(tables)
        except (
            OSError,
            ValueError,
            KeyError,
            IndexError,
            TypeError,
            pdfplumber.utils.exceptions.PdfminerException,
        ) as e:  # a broken PDF is a row, not a crash
            layout, recs, pages = "error", [], 0
            errors.append((name, str(e)[:80]))
        base = {
            "pdf_name": name,
            "pdf_key": name.split("__", 1)[1][: -len(".pdf")],
            "pdf_sha256": m["sha256"],
            "pdf_pages": pages,
            "layout": layout,
        }
        if not recs:
            rows.append({**base, "record_no": 0, "parse_status": "layout_unknown"})
            stat[(layout, "layout_unknown")] += 1
        for k, r in enumerate(recs, 1):
            rows.append(
                {
                    **base,
                    "record_no": k,
                    **{c: r.get(c) for c in COLS},
                    "parse_status": r["parse_status"],
                }
            )
            stat[(layout, r["parse_status"])] += 1
        if n % 500 == 0:
            print(n, dict(stat), flush=True)
    df = pd.DataFrame(rows)
    df["extra_cells"] = df["extra_cells"].map(
        lambda v: json.dumps(v, ensure_ascii=False) if isinstance(v, dict) else None
    )
    (ROOT / "data" / "parquet").mkdir(parents=True, exist_ok=True)
    df.to_parquet(
        ROOT / "data" / "parquet" / "pdf_records_as_read.parquet",
        compression="zstd",
        index=False,
    )
    log = {"pdfs": int((pd.Series([m["status"] for m in man.values()]) == 200).sum()), "records": len(df),
           "by_layout_status": {f"{a}/{b}": v for (a, b), v in sorted(stat.items())}, "errors": errors}  # fmt: skip
    (ROOT / "docs" / "pdf_parse_log.json").write_text(
        json.dumps(log, ensure_ascii=False, indent=1) + "\n"
    )
    print(log)
    return 0


if __name__ == "__main__":
    sys.exit(main())
