#!/usr/bin/env python3
"""Second route for the PDF table: every parsed cell must appear in `pdftotext -layout` of the same PDF (whitespace removed),
and the number of 管理番号 / 整理番号 labels in that text must equal the number of parsed records of the PDF.

    uv run python -u scripts/09_verify_pdf.py     # docs/pdf_verify.json, exit 1 when a parsed cell is not in the text
"""

import json
import re
import subprocess
import sys

import kansui
import pandas as pd

ROOT = kansui.root()
FIELDS = ["mgmt_no", "place_name", "road_name", "underpass_name", "road_kind", "pref_name", "municipality", "aza_chome",
          "banchi", "sakimei", "manager_name", "manager_tel", "police_name", "police_tel", "fire_name", "fire_tel"]  # fmt: skip


def squash(s: str) -> str:
    return re.sub(r"\s+", "", s)


def main() -> int:
    run = max((ROOT / "data" / "raw").glob("*/MANIFEST.json")).parent
    df = pd.read_parquet(ROOT / "data" / "parquet" / "pdf_records.parquet")
    bad, checked_cells, label_mismatch = [], 0, []
    for name, g in df[df["layout"].isin(["A", "B"])].groupby("pdf_name"):
        text = squash(
            subprocess.run(
                ["pdftotext", "-layout", str(run / "pdf" / name), "-"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout
        )
        labels = text.count("管理番号") + text.count("整理番号")
        if labels != len(g):
            label_mismatch.append((name, labels, len(g)))
        for _, r in g.iterrows():
            for f in FIELDS:
                v = r.get(f)
                if isinstance(v, str):
                    checked_cells += 1
                    # pdftotext -layout puts the other cells of the row between the lines of a cell that wraps (and between
                    # the two lines of a split identifier): check each whitespace-separated piece of the cell
                    parts = v.rsplit("-", 1) if f == "mgmt_no" else v.split()
                    if any(squash(x) not in text for x in parts):
                        bad.append((name, f, v))
    res = {"pdfs_checked": int(df[df["layout"].isin(["A", "B"])]["pdf_name"].nunique()), "cells_checked": checked_cells,
           "cells_not_in_pdftotext": len(bad), "label_count_mismatch": len(label_mismatch),
           "examples_not_in_text": bad[:20], "examples_label_mismatch": label_mismatch[:20]}  # fmt: skip
    (ROOT / "docs" / "pdf_verify.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1) + "\n"
    )
    print({k: v for k, v in res.items() if not k.startswith("examples")})
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
