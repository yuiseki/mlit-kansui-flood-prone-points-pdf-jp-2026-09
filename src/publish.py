#!/usr/bin/env python3
"""Push the card, licence, provenance, the KML files as fetched, the Parquet, the evidence and the docs to the Hub in one commit.

uv run python src/publish.py             # dry run: list the files and their sizes
uv run python src/publish.py --push      # prints the commit sha and writes docs/revision.json

Refuses to run unless docs/licence_status.json says that PDL1.0 was confirmed from a saved source.
"""

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
REPO = "yuiseki/mlit-kansui-flood-prone-points-pdf-jp-2026-09"
DOCS = [
    "licence_status.json",
    "bureau_terms.json",
    "pdf_parse_log.json",
    "pdf_verify.json",
    "attach_log.json",
    "manual_check.json",
    "manual_check_sample.tsv",
]


def licence_ok(status: dict, man_files: dict, layers: list[str], card: str) -> bool:
    """True only when the card says PDL1.0 and every bureau that has a layer in the table is confirmed."""
    return "license_name: pdl-1.0" in card and all(
        status.get(man_files[layer]["bureau"], {}).get("confirmed") is True
        for layer in layers
    )


def collect() -> dict[str, Path]:
    st = json.loads((ROOT / "docs" / "licence_status.json").read_text())["bureaus"]
    card = (DATA / "README.md").read_text(encoding="utf-8")
    log = json.loads((ROOT / "docs" / "export_log.json").read_text())
    run = max((DATA / "raw").glob("*/MANIFEST.json")).parent
    man = json.loads((run / "MANIFEST.json").read_text())
    layers = [
        layer for layer in man["files"] if layer in log["files"]
    ]  # the layers that are in the table
    if not licence_ok(st, man["files"], layers, card):
        raise SystemExit("the licence is not confirmed: do not publish")
    if "4,410" not in card or "4,525" not in card:
        raise SystemExit("the card does not match the tables")
    files = {"README.md": DATA / "README.md", "LICENSE": DATA / "LICENSE", "provenance.yaml": DATA / "provenance.yaml",
             f"raw/{run.name}/MANIFEST.json": run / "MANIFEST.json",
             f"raw/{run.name}/PDF_MANIFEST.json": run / "PDF_MANIFEST.json",
             "parquet/pdf_records.parquet": DATA / "parquet" / "pdf_records.parquet",
             "parquet/point_pdf.parquet": DATA / "parquet" / "point_pdf.parquet"}  # fmt: skip
    for sub in ("pages", "terms"):
        for p in sorted((ROOT / "evidence" / sub).glob("*")):
            files[f"evidence/{sub}/{p.name}"] = p
    for d in DOCS:
        files[f"docs/{d}"] = ROOT / "docs" / d
    for s in sorted((ROOT / "scripts").glob("*.py")):
        files[f"scripts/{s.name}"] = s
    missing = [k for k, v in files.items() if not v.is_file()]
    if missing:
        raise SystemExit(f"missing: {missing}")
    return files


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=REPO)
    ap.add_argument("--push", action="store_true")
    a = ap.parse_args()
    files = collect()
    total = sum(p.stat().st_size for p in files.values())
    print(f"{a.repo}\n  {len(files)} files, {total:,} bytes")
    if not a.push:
        print("\ndry run. pass --push to upload")
        return 0
    from huggingface_hub import CommitOperationAdd, HfApi

    api = HfApi()
    api.create_repo(a.repo, repo_type="dataset", exist_ok=True, private=False)
    ops = [
        CommitOperationAdd(path_in_repo=k, path_or_fileobj=str(p))
        for k, p in files.items()
    ]
    info = api.create_commit(a.repo, ops, repo_type="dataset", commit_message="Tables read from the 箇所表 PDFs of the flood-prone road points (冠水想定箇所) of the MLIT bureaus")  # fmt: skip
    sums = {k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in files.items()}
    (ROOT / "docs" / "revision.json").write_text(
        json.dumps({"repo": a.repo, "revision": info.oid, "sha256": sums}, indent=1)
        + "\n"
    )
    print("pushed", a.repo, "revision", info.oid)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
