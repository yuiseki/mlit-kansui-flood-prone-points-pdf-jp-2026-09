#!/usr/bin/env python3
"""Read the repository back from the Hub at the recorded revision and compare it with the local copy:
file checksums, rows, schema, CRS, value counts, NULL counts and the cells themselves.

    uv run python scripts/06_verify_hub.py   # needs docs/revision.json from src/publish.py --push
"""

import hashlib
import json
import sys
from pathlib import Path

import geopandas as gpd
import kansui
from huggingface_hub import hf_hub_download

ROOT = kansui.root()


def main() -> int:
    rev = json.loads((ROOT / "docs" / "revision.json").read_text())
    repo, sha = rev["repo"], rev["revision"]
    out, bad = {"repo": repo, "revision": sha}, []
    cache = ROOT / "data" / "hub_readback"
    for name, want in rev["sha256"].items():
        p = hf_hub_download(
            repo, name, repo_type="dataset", revision=sha, local_dir=cache
        )
        if hashlib.sha256(Path(p).read_bytes()).hexdigest() != want:
            bad.append(f"checksum {name}")
    out["files_checked"] = len(rev["sha256"])
    hub = gpd.read_parquet(cache / "parquet" / "kansui_points.parquet")
    mine = gpd.read_parquet(ROOT / "data" / "parquet" / "kansui_points.parquet")
    ver = json.loads((ROOT / "docs" / "verify_local.json").read_text())
    out["rows"], out["crs"] = len(hub), hub.crs.to_string()
    out["bbox"] = [float(x) for x in hub.total_bounds]
    if (
        len(hub) != ver["rows"]
        or list(hub.columns) != list(mine.columns)
        or hub.crs != mine.crs
    ):
        bad.append("rows, columns or CRS")
    if (
        not hub.drop(columns="geometry").equals(mine.drop(columns="geometry"))
        or not hub.geometry.geom_equals(mine.geometry).all()
    ):
        bad.append("cells differ from the local copy")
    out["per_prefecture"] = {
        k: int(v) for k, v in hub.groupby("pref_code").size().items()
    }
    out["nulls"] = {c: int(hub[c].isna().sum()) for c in hub.columns}
    out["null_geometry"] = int(hub.geometry.isna().sum())
    out["problems"] = bad
    (ROOT / "docs" / "verify_hub.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n"
    )
    print(
        json.dumps(
            {k: v for k, v in out.items() if k != "per_prefecture"},
            ensure_ascii=False,
            indent=1,
        )
    )
    print(
        "OK: the repository at",
        sha,
        "equals the local copy" if not bad else f"has problems: {bad}",
    )
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
