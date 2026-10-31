#!/usr/bin/env python3
"""Read the Hub repository back at the recorded revision and compare it with the local copy: the checksums of every published file,
and the row counts, schema, non-null counts and cells of the two Parquet tables.

    uv run python scripts/12_verify_hub.py   # needs docs/revision.json from src/publish.py --push
"""

import json
import sys
from pathlib import Path

import pandas as pd
from huggingface_hub import hf_hub_download
from publish_helpers import sha256

ROOT = Path(__file__).parents[1]


def main() -> int:
    rev = json.loads((ROOT / "docs" / "revision.json").read_text())
    repo, sha = rev["repo"], rev["revision"]
    bad = []
    for name, want in rev["sha256"].items():
        got = sha256(Path(hf_hub_download(repo, name, repo_type="dataset", revision=sha)))
        if got != want:
            bad.append(("checksum", name))
    for t in ("pdf_records", "point_pdf"):
        a = pd.read_parquet(hf_hub_download(repo, f"parquet/{t}.parquet", repo_type="dataset", revision=sha))
        b = pd.read_parquet(ROOT / "data" / "parquet" / f"{t}.parquet")
        if list(a.columns) != list(b.columns) or len(a) != len(b):
            bad.append(("shape", t))
        elif not a.reset_index(drop=True).equals(b.reset_index(drop=True)):
            bad.append(("cells", t))
        elif a.notna().sum().to_dict() != b.notna().sum().to_dict():
            bad.append(("non-null", t))
        print(t, len(a), "rows,", len(a.columns), "columns")
    for x in bad:
        print("DIFF", x)
    print("OK: the repository at", sha, "equals the local copy" if not bad else "DIFFERS")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
