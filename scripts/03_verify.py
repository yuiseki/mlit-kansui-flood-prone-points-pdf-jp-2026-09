#!/usr/bin/env python3
"""Check the Parquet against the KML files with a second reader (GDAL's KML driver through pyogrio).

uv run python scripts/03_verify.py     # docs/verify_local.json, exit 1 on any difference
"""

import hashlib
import json
import sys

import geopandas as gpd
import kansui
import numpy as np
import pandas as pd
import pyogrio

ROOT = kansui.root()


def main() -> int:
    run = max((ROOT / "data" / "raw").glob("*/MANIFEST.json")).parent
    man = json.loads((run / "MANIFEST.json").read_text())
    mine = gpd.read_parquet(ROOT / "data" / "parquet" / "kansui_points.parquet")
    problems, per = [], {}
    for layer, m in man["files"].items():
        p = run / "kml" / f"{layer}.kml"
        if hashlib.sha256(p.read_bytes()).hexdigest() != m["sha256"]:
            problems.append(f"sha256 of {layer}")
        # the KML driver exposes every <Style>-named group of Placemarks as a layer: read them all
        parts = [
            pyogrio.read_dataframe(p, layer=ln) for ln, _ in pyogrio.list_layers(p)
        ]
        ogr = pd.concat([x[x.geometry.notna()] for x in parts], ignore_index=True)
        sub = mine[mine["layer"] == layer].reset_index(drop=True)
        per[layer] = {"ogr": len(ogr), "mine": len(sub)}
        if len(ogr) != len(sub):
            problems.append(f"count {layer}: ogr {len(ogr)} mine {len(sub)}")
            continue
        a = sorted(
            zip(
                ogr["Name"].str.strip(),
                ogr.geometry.x.round(9),
                ogr.geometry.y.round(9),
            )
        )
        b = sorted(zip(sub["name"], sub["lon"].round(9), sub["lat"].round(9)))
        if a != b:
            problems.append(f"(name, lon, lat) multisets differ in {layer}")
        sg = sub.geometry
        if (
            np.abs(sg.x.to_numpy() - sub["lon"].to_numpy()).max() > 0
            or np.abs(sg.y.to_numpy() - sub["lat"].to_numpy()).max() > 0
        ):
            problems.append(f"geometry differs from lon/lat in {layer}")
    res = {
        "rows": len(mine), "ogr_rows": sum(v["ogr"] for v in per.values()),
        "per_layer": per, "unique_fid": bool(mine["fid"].is_unique),
        "crs": mine.crs.to_string(), "null_geometry": int(mine.geometry.isna().sum()),
        "problems": problems,
    }  # fmt: skip
    (ROOT / "docs" / "verify_local.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1)
    )
    print({k: v for k, v in res.items() if k != "per_layer"})
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
