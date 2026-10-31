#!/usr/bin/env python3
"""Sanity check: does each point lie in the prefecture its layer names? (yuiseki/jp-admin-2026-09, JGD2000 polygons)

    uv run python scripts/05_check_prefecture.py     # docs/prefecture_check.json, docs/prefecture_outliers.tsv

A point outside its prefecture polygon is reported with the distance to it (the polygons are of the administrative
areas, so a point on a pier or a shore can lie a few metres outside). The data are not changed by this check.
"""

import json

import geopandas as gpd
import kansui
import numpy as np
from huggingface_hub import hf_hub_download

ROOT = kansui.root()
PLANE = 6677  # only for metre distances


def main() -> int:
    pts = gpd.read_parquet(ROOT / "data" / "parquet" / "kansui_points.parquet")
    pref = gpd.read_parquet(
        hf_hub_download(
            "yuiseki/jp-admin-2026-09", "prefectures.parquet", repo_type="dataset"
        )
    )
    pref = pref.set_index("pref_code")
    inside, dist = [], []
    for code, sub in pts.groupby("pref_code"):
        poly = pref.loc[code, "geometry"]
        ins = sub.geometry.within(poly)
        inside.extend(zip(sub.index, ins))
        out = sub[~ins]
        if len(out):
            pa = gpd.GeoSeries([poly], crs=pref.crs).to_crs(PLANE).iloc[0]
            d = out.geometry.set_crs(4326).to_crs(PLANE).distance(pa)
            dist.extend(zip(out.index, d))
    pts["in_prefecture"] = False
    for i, v in inside:
        pts.loc[i, "in_prefecture"] = bool(v)
    pts["dist_m"] = np.nan
    for i, d in dist:
        pts.loc[i, "dist_m"] = float(d)
    out = pts[~pts["in_prefecture"]].sort_values("dist_m", ascending=False)
    out[["fid", "layer", "pref", "name", "lon", "lat", "dist_m"]].to_csv(
        ROOT / "docs" / "prefecture_outliers.tsv", sep="\t", index=False
    )
    res = {
        "points": len(pts), "inside": int(pts["in_prefecture"].sum()), "outside": len(out),
        "outside_over_100m": int((out["dist_m"] > 100).sum()), "outside_over_1km": int((out["dist_m"] > 1000).sum()),
        "max_dist_m": float(out["dist_m"].max()) if len(out) else 0.0,
        "per_layer_outside": out.groupby("layer").size().to_dict(),
    }  # fmt: skip
    (ROOT / "docs" / "prefecture_check.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1)
    )
    print(res)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
