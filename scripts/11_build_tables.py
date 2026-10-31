#!/usr/bin/env python3
"""Write the two tables of this dataset from the parse and the attach step.

    uv run python scripts/11_build_tables.py   # data/parquet/pdf_records.parquet, point_pdf.parquet

pdf_records: one row per PDF, the cells as read (pdf_records_as_read.parquet, from 08_parse_pdfs.py), plus `pdf_url` (the PDF at
the bureau), `bureau` (the prefix of the file name) and `name_cells`. Some PDFs print the reading (furigana) of the names above
them, and the text of the name cells then runs the reading into the name: in such a record `place_name`, `underpass_name` and
`road_kind` are null and `name_cells` says `withheld_furigana_in_source` (else `as_read`).
point_pdf: one row per KML point (no geometry): the key and URL of its PDF and how it was matched. Join with the points on `fid`.
"""

import json
import re

import geopandas as gpd
import kansui
import pandas as pd

ROOT = kansui.root()
NAME_COLS = ["place_name", "underpass_name", "road_kind"]


def has_furigana(v) -> bool:
    return isinstance(v, str) and bool(re.match(r"^[ぁ-ん]+\s", v) or re.search(r"[ぁ-ん]\s[ぁ-ん]", v))


def main() -> int:
    run = max((ROOT / "data" / "raw").glob("*/PDF_MANIFEST.json"))
    urls = {k: v["url"] for k, v in json.loads(run.read_text())["files"].items()}
    rec = pd.read_parquet(ROOT / "data" / "parquet" / "pdf_records_as_read.parquet")
    rec["bureau"] = rec["pdf_name"].str.split("__").str[0]
    rec.insert(1, "pdf_url", rec["pdf_name"].map(urls))
    furi = rec[NAME_COLS].apply(lambda c: c.map(has_furigana)).any(axis=1) & (rec["layout"] != "unknown")
    rec.loc[furi, NAME_COLS] = None
    rec["name_cells"] = furi.map({True: "withheld_furigana_in_source", False: "as_read"})
    joined = gpd.read_parquet(ROOT / "data" / "parquet" / "kansui_points_joined.parquet")
    pts = pd.DataFrame(joined[["fid", "layer", "pref", "name", "pdf_name", "pdf_key", "pdf_match", "pdf_key_consistent"]])
    pts.insert(4, "pdf_url", pts["pdf_name"].map(urls))
    out = ROOT / "data" / "parquet"
    rec.to_parquet(out / "pdf_records.parquet", compression="zstd", index=False)
    pts.to_parquet(out / "point_pdf.parquet", compression="zstd", index=False)
    print(len(rec), "records,", int(furi.sum()), "with furigana;", len(pts), "points")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
