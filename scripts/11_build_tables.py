#!/usr/bin/env python3
"""Write the two tables of this dataset from the parse and the attach step.

    uv run python scripts/11_build_tables.py   # data/parquet/pdf_records.parquet, point_pdf.parquet

pdf_records: one row per PDF, the cells as read (see 08_parse_pdfs.py), plus `bureau` (the prefix of the file name) and
`name_cells_have_furigana`: the PDF prints the reading of the names above them, and the text of the cell may then
begin with, or hold, the reading (the cell is not corrected; the flag only marks it).
point_pdf: one row per KML point (no geometry): the key of its PDF and how it was matched. Join with the points on `fid`.
"""

import re

import geopandas as gpd
import kansui
import pandas as pd

ROOT = kansui.root()
NAME_COLS = ["place_name", "underpass_name", "road_kind"]


def has_furigana(v) -> bool:
    return isinstance(v, str) and bool(re.match(r"^[ぁ-ん]+\s", v) or re.search(r"[ぁ-ん]\s[ぁ-ん]", v))


def main() -> int:
    rec = pd.read_parquet(ROOT / "data" / "parquet" / "pdf_records.parquet")
    rec["bureau"] = rec["pdf_name"].str.split("__").str[0]
    rec["name_cells_have_furigana"] = rec[NAME_COLS].apply(lambda c: c.map(has_furigana)).any(axis=1)
    rec.loc[rec["layout"] == "unknown", "name_cells_have_furigana"] = False
    joined = gpd.read_parquet(ROOT / "data" / "parquet" / "kansui_points_joined.parquet")
    pts = pd.DataFrame(joined[["fid", "layer", "pref", "name", "pdf_name", "pdf_key", "pdf_match", "pdf_key_consistent"]])
    out = ROOT / "data" / "parquet"
    rec.to_parquet(out / "pdf_records.parquet", compression="zstd", index=False)
    pts.to_parquet(out / "point_pdf.parquet", compression="zstd", index=False)
    print(len(rec), "records,", int(rec["name_cells_have_furigana"].sum()), "with furigana;", len(pts), "points")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
