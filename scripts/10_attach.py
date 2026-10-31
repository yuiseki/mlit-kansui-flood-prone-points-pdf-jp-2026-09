#!/usr/bin/env python3
"""Attach the parsed PDF attributes to the points by the PDF file (and say how each point was matched).

    uv run python scripts/10_attach.py     # data/parquet/kansui_points_joined.parquet, docs/attach_log.json,
                                           # docs/manual_check_sample.tsv (30 points, seed 20261030)

match: pdf_unique        the point's PDF is linked by this point only and holds exactly one record
       pdf_shared        the PDF is linked by several points or holds several records: attributes are not attached
       no_pdf            the KML has no link
       pdf_missing       the PDF is not available (404) or not parsed
Columns of the PDF table are prefixed `pdf_`; pdf_parse_status is the status of the record.
"""

import json
import re
import sys

import geopandas as gpd
import numpy as np
import kansui
import pandas as pd

ROOT = kansui.root()
PDF_COLS = ["layout", "record_no", "mgmt_no", "place_name", "road_name", "underpass_name", "road_kind", "pref_name", "municipality",
            "aza_chome", "banchi", "sakimei", "manager_name", "manager_tel", "manager_tel_text", "police_name", "police_tel",
            "police_text", "fire_name", "fire_tel", "fire_text", "remarks", "extra_cells", "parse_status"]  # fmt: skip


NAME_COLS = ["place_name", "underpass_name", "road_kind"]


def has_furigana(v) -> bool:
    return isinstance(v, str) and bool(re.match(r"^[ぁ-ん]+\s", v) or re.search(r"[ぁ-ん]\s[ぁ-ん]", v))


def last_number(s) -> str | None:
    m = re.findall(r"\d+", s) if isinstance(s, str) else []
    return str(int(m[-1])) if m else None


def main() -> int:
    pts = gpd.read_parquet(ROOT / "data" / "parquet" / "kansui_points.parquet")
    rec = pd.read_parquet(ROOT / "data" / "parquet" / "pdf_records_as_read.parquet")
    pts["pdf_name"] = [
        kansui.pdf_name(u) if isinstance(u, str) else None for u in pts["pdf_url"]
    ]
    per_pdf_points = pts.groupby("pdf_name")["fid"].transform("size")
    per_pdf_records = rec.groupby("pdf_name")["record_no"].apply(
        lambda s: int((s > 0).sum())
    )
    pts["_np"], pts["_nr"] = per_pdf_points, pts["pdf_name"].map(per_pdf_records)
    pts["pdf_match"] = "pdf_unique"
    pts.loc[pts["pdf_name"].isna(), "pdf_match"] = "no_pdf"
    pts.loc[pts["pdf_name"].notna() & pts["_nr"].isna(), "pdf_match"] = "pdf_missing"
    pts.loc[
        (pts["pdf_match"] == "pdf_unique") & ((pts["_np"] > 1) | (pts["_nr"] != 1)),
        "pdf_match",
    ] = "pdf_shared"
    one = rec[rec["record_no"] == 1].set_index("pdf_name")
    ren = {c: f"pdf_{c}" for c in PDF_COLS}
    attrs = one[PDF_COLS].rename(columns=ren)
    # Some bureaus print the reading (furigana) of the names above them: the PDF text then runs the reading into the
    # name cells and the name cannot be told from the reading without guessing. Those three cells are not published.
    furi = attrs[[f"pdf_{c}" for c in NAME_COLS]].apply(lambda col: col.map(has_furigana)).any(axis=1)
    for c in NAME_COLS:
        attrs.loc[furi, f"pdf_{c}"] = None
    attrs["pdf_name_cells"] = np.where(furi, "furigana_in_source_not_published", "as_published")
    out = pts.join(attrs, on="pdf_name")
    keep = out["pdf_match"] == "pdf_unique"
    for c in [*ren.values(), "pdf_name_cells"]:
        out.loc[~keep, c] = None
    out["pdf_parse_status"] = out["pdf_parse_status"].where(keep, None)
    # consistency of the number in the file name with the number in the management number (a check, not a filter)
    out["pdf_key_consistent"] = [
        (last_number(k) == last_number(m)) if (keep_i and isinstance(m, str)) else None
        for k, m, keep_i in zip(out["pdf_key"], out["pdf_mgmt_no"], keep, strict=True)
    ]
    out = out.drop(columns=["_np", "_nr"])
    out = gpd.GeoDataFrame(out, geometry="geometry", crs=4326)
    out.to_parquet(
        ROOT / "data" / "parquet" / "kansui_points_joined.parquet",
        compression="zstd",
        write_covering_bbox=True,
        index=False,
    )
    log = {
        "points": len(out), "match": out["pdf_match"].value_counts().to_dict(),
        "parse_status_of_matched": out.loc[keep, "pdf_parse_status"].value_counts(dropna=False).to_dict(),
        "layout_of_matched": out.loc[keep, "pdf_layout"].value_counts(dropna=False).to_dict(),
        "attributes_ok": int((out["pdf_parse_status"] == "ok").sum()),
        "key_consistent": out["pdf_key_consistent"].value_counts(dropna=False).astype(int).to_dict(),
    }  # fmt: skip
    log["key_consistent"] = {str(k): v for k, v in log["key_consistent"].items()}
    (ROOT / "docs" / "attach_log.json").write_text(
        json.dumps(log, ensure_ascii=False, indent=1) + "\n"
    )
    ok = out[out["pdf_parse_status"] == "ok"]
    sample = ok.sample(n=min(30, len(ok)), random_state=20261030).sort_values("fid")
    sample[["fid", "pref", "name", "pdf_name", "pdf_layout", "pdf_mgmt_no", "pdf_place_name", "pdf_road_name", "pdf_underpass_name",
            "pdf_road_kind", "pdf_municipality", "pdf_aza_chome", "pdf_manager_name", "pdf_police_name", "pdf_fire_name"]].to_csv(
        ROOT / "docs" / "manual_check_sample.tsv", sep="\t", index=False
    )  # fmt: skip
    print(log)
    return 0


if __name__ == "__main__":
    sys.exit(main())
