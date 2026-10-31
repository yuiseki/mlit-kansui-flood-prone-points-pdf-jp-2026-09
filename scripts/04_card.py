#!/usr/bin/env python3
"""Write data/README.md (the Hub card), data/LICENSE and data/provenance.yaml from the generated docs.

    uv run python scripts/04_card.py

The licence block is PDL1.0 only for bureaus that docs/licence_status.json (written by 00_terms.py) confirms.
"""

import json

import geopandas as gpd
import pandas as pd
import kansui

ROOT = kansui.root()
REPO = "mlit-kansui-flood-prone-points-pdf-jp-2026-09"


BUREAU_NAMES = [
    "東北地方整備局",
    "関東地方整備局",
    "北陸地方整備局",
    "中部地方整備局",
    "近畿地方整備局",
    "四国地方整備局",
    "九州地方整備局",
    "中国地方整備局",
]


def bureau_ids() -> list[str]:
    return ["thr", "ktr", "hrr", "cbr", "kkr", "skr", "qsr", "cgr"]


def main() -> int:
    st = json.loads((ROOT / "docs" / "licence_status.json").read_text())
    bt = json.loads((ROOT / "docs" / "bureau_terms.json").read_text())
    run = max((ROOT / "data" / "raw").glob("*/MANIFEST.json")).parent
    man = json.loads((run / "MANIFEST.json").read_text())
    g = gpd.read_parquet(ROOT / "data" / "parquet" / "kansui_points.parquet")
    ex = json.loads((ROOT / "docs" / "export_log.json").read_text())
    chk = json.loads((ROOT / "docs" / "prefecture_check.json").read_text())
    al = json.loads((ROOT / "docs" / "attach_log.json").read_text())
    pl = json.loads((ROOT / "docs" / "pdf_parse_log.json").read_text())
    pv = json.loads((ROOT / "docs" / "pdf_verify.json").read_text())
    mc = json.loads((ROOT / "docs" / "manual_check.json").read_text())
    rec = pd.read_parquet(ROOT / "data" / "parquet" / "pdf_records.parquet")
    pts = pd.read_parquet(ROOT / "data" / "parquet" / "point_pdf.parquet")
    rok = rec[rec["parse_status"] == "ok"]
    nfur = int((rec["name_cells"] != "as_read").sum())
    fur_pts = int(pts["pdf_name"].isin(rec.loc[rec["name_cells"] != "as_read", "pdf_name"]).sum())
    fur_pref = ", ".join(
        f"{k} {v}"
        for k, v in pts[pts["pdf_name"].isin(rec.loc[rec["name_cells"] != "as_read", "pdf_name"])]["pref"].value_counts().items()
    )
    nmg = int((~rok["mgmt_no"].astype(str).str.match(r"^.{2,4}[都道府県]-\d\d-\d{1,3}(-\d)?$")).sum())
    nf = int((pts["pdf_key_consistent"] == False).sum())  # noqa: E712
    pman = json.loads((run / "PDF_MANIFEST.json").read_text())["files"]
    n404 = sum(1 for v in pman.values() if v["status"] == 404)
    layouts = "\n".join(f"| {k} | {v} |" for k, v in pl["by_layout_status"].items())
    matches = "\n".join(f"| {k} | {v} |" for k, v in al["match"].items())
    pman_last = ""
    ex0 = json.loads((ROOT / "docs" / "export_log.json").read_text())
    bureaus_in = sorted(
        {m["bureau"] for layer, m in man["files"].items() if layer in ex0["files"]}
    )
    all_ok = all(st["bureaus"][b]["confirmed"] for b in bureaus_in)
    if all_ok:
        lic = "license: other\nlicense_name: pdl-1.0\nlicense_link: https://www.digital.go.jp/resources/open_data/public_data_license_v1.0"
    else:
        lic = "license: other\nlicense_name: unconfirmed"
    names = dict(zip(bureau_ids(), BUREAU_NAMES))
    bases = kansui.parse_bases(
        (ROOT / "data" / "bases_from_user.txt").read_text()
        + (ROOT / "data" / "bases_added.txt").read_text()
    )
    page = {}
    for base in bases.values():
        page.setdefault(
            kansui.bureau_of(base),
            base.replace("http://", "https://") + "/main/index.html",
        )
    quotes = "\n".join(
        f"- {names[b]} ({bt[b]['url']}):\n  > {bt[b]['use_sentence']}"
        for b in bureaus_in
    )
    attrib = "\n".join(
        f"- {names[b]}: 出典：{names[b]}ホームページ（{page[b]}）" for b in bureaus_in
    )
    proc = "\n".join(
        f"- {names[b]}: 「道路防災情報Webマップ 冠水想定箇所」（{names[b]}）（{page[b]}）を加工して作成"
        for b in bureaus_in
    )
    lic_text = f"""Each bureau's own site-wide terms say that its content is usable under the Public Data License 1.0
(公共データ利用規約 第1.0版, PDL1.0; compatible with CC BY 4.0), unless a right notice says otherwise. **The basis is the
bureaus' site-wide terms. No licence notice specific to the Webmap pages or the KML files exists** (the Webmap pages,
their scripts and the KML carry no rights notice: checked {man["fetched"]}). Judge for yourself whether the site-wide
terms reach these files. The pages were saved under `evidence/terms/`; the quotations are in `docs/bureau_terms.json`.

The Kinki (近畿) sentence, from <https://www.kkr.mlit.go.jp/link.html>:

> {bt["kkr"]["use_sentence"]}

The sentence of each bureau whose points are in this dataset:

{quotes}

The terms exclude symbol marks, logos and character designs, and content for which a separate rule is stated
(the Kyushu page adds that some content may be restricted by individual laws). The background map of the Webmaps is
the GSI's 地理院地図 and is not part of the data. The 箇所表 PDFs (not included here) hold GSI maps and photographs of
the sites; no rights mark other than the GSI map note was found on the 40 PDFs that were looked at.

Attribution, per bureau (出典：<局>ホームページ（URL）):

{attrib}

Processing notice (編集・加工等を行ったことの記載。国が作成したかのような態様で公表・利用してはいけません):

{proc}

This dataset is made by yuiseki from the bureaus' PDFs: their tables were read as text and written as Parquet; the text of the
PDFs is kept as read. It was made by processing the bureaus' data and is not made or endorsed by the State. The licence basis is the
bureaus' site-wide terms, as for the KML; no rights notice specific to the PDFs was found other than the GSI map note (checked on 40 of
them), and the PDFs are not redistributed.
"""
    by_pref = g.groupby("pref").size()
    rows = "\n".join(f"| {p} | {n} |" for p, n in by_pref.items())
    bureaus = "\n".join(
        f"| {b} | {n} |" for b, n in g.groupby("bureau_ja").size().items()
    )
    card = f"""---
{lic}
language:
- ja
tags:
- japan
- flood
- road
- underpass
- point
size_categories:
- 1K<n<10K
pretty_name: Tables read from the 箇所表 PDFs of the flood-prone road points (冠水想定箇所) of the MLIT regional bureaus
configs:
- config_name: pdf_records
  data_files: parquet/pdf_records.parquet
- config_name: point_pdf
  data_files: parquet/point_pdf.parquet
---

# {REPO}

The tables of the 箇所表 PDFs that the KML points of 冠水想定箇所 link to (road points where the road lies lower than the
ground around it, for example underpasses): the management number, the road, the underpass name, the address, the manager, the police
and fire stations. They are from the 道路防災情報Webマップ of eight regional bureaus of the Ministry of Land, Infrastructure,
Transport and Tourism (MLIT). **This is text read from PDFs and it is uncertain**: read the sections "How it was read" and
"Known issues". The points themselves, with their coordinates, are a separate dataset made from the KML files,
[mlit-kansui-flood-prone-points-jp-2026-09](https://huggingface.co/datasets/yuiseki/mlit-kansui-flood-prone-points-jp-2026-09);
the two join on `pdf_key` (or on `fid`, which is the row number of that dataset).

**The PDFs are not in this dataset and are not redistributed.** They hold GSI maps and photographs of the sites. Only the text of
the tables is here, and for each PDF its URL, size, Last-Modified and sha256, so that a reader can fetch the PDF from the bureau and
check the reading.

## Source

The PDF of each point is linked from its KML Placemark (`pdf_url` of the points dataset). {len(pman):,} unique PDFs are linked (some by several points). They were fetched on 2026-10-30 and 2026-10-31
(`fetched_all` of `PDF_MANIFEST.json`), one request at a time with a 2 s pause; {n404} of them are missing (HTTP 404).
The KML files are described in the points dataset.

## Files

| File | Rows | What a row is |
|---|---|---|
| `parquet/pdf_records.parquet` | {len(rec):,} | A PDF that was read (one record each); the cells as read, except the withheld ones |
| `parquet/point_pdf.parquet` | {len(pts):,} | A KML point: the key of its PDF and how it was matched |
| `raw/*/PDF_MANIFEST.json` | {len(pman):,} | A PDF: URL, status, size, Last-Modified, sha256 |

`pdf_records`: `pdf_name` (the file name used locally, `<bureau>__<stem>.pdf`), `pdf_url` (the PDF at the bureau), `pdf_key` (the stem; the key of the points
dataset), `pdf_sha256`, `pdf_pages`, `layout`, `record_no`, `mgmt_no` (管理番号/整理番号), `place_name` (箇所名称), `road_name` (道路名),
`underpass_name` (アンダーパス等名称/施設名), `road_kind` (種別), `pref_name`, `municipality` (市町村), `aza_chome` (字丁目), `banchi`
(番地), `sakimei` (地先名), `manager_name`/`manager_tel` (管理者), `manager_tel_text`, `police_name`/`police_tel`/`police_text`,
`fire_name`/`fire_tel`/`fire_text`, `remarks` (備考), `extra_cells` (JSON: the extra items of some forms, 冠水範囲, 冠水原因, 排水ポンプの有無 ...),
`parse_note`, `parse_status`, `bureau`, `name_cells` (`as_read`, or `withheld_furigana_in_source`: see Known issues). In layout B the police and fire cells hold name and TEL together as
published (`*_text`), and the manager's further cells are in `manager_tel_text`.

`point_pdf`: `fid`, `layer`, `pref`, `name`, `pdf_name`, `pdf_url`, `pdf_key`, `pdf_match`, `pdf_key_consistent`.

## How it was read

The tables were read with pdfplumber, **the text of every cell as published (only whitespace collapsed)**. A cell that could not be
read with certainty is null; nothing was guessed, and no language model was used. `scripts/08_parse_pdfs.py` is the reader and
`tests/test_pdfparse.py` its tests.

| layout / parse_status | PDFs (records) |
|---|---|
{layouts}

`parse_status`: `ok` (all required cells read), `ambiguous` (a required cell is empty or unreadable; see `parse_note`),
`layout_unknown` (no known layout; all attributes null). Layout A: the 説明表 / 箇所表 / 様式 tables; layout B: the
道路冠水(危険)想定箇所 forms (石川, 富山, 新潟).

How the points are matched to the table (`pdf_match`; the key is the PDF file linked in the KML):

| pdf_match | points |
|---|---|
{matches}

`pdf_unique`: the PDF is linked by this point only and holds one record, so its record is the point's; `pdf_shared`: the PDF is linked
by several points or holds several records, and it is not said which record is which point; `no_pdf`; `pdf_missing`.
`pdf_key_consistent` compares the number in the file name with the number in the management number (a check only; false for {nf:,}
points that have a record).

Checks: {pv["cells_checked"]:,} parsed cells of {pv["pdfs_checked"]} PDFs were looked up in `pdftotext -layout` of the same PDF
({pv["cells_not_in_pdftotext"]} not found, all management numbers that the PDF breaks over two lines; the count of 管理番号/整理番号
labels equals the record count except {pv["label_count_mismatch"]} PDFs). Manual check: {mc["n"]} points drawn at random (seed
{mc["seed"]}) were compared with the text of their PDFs (before the furigana cells were withheld): {mc["correct"]} of {mc["n"]} had every
cell matching the PDF text ({mc["note"]}). `docs/manual_check_sample.tsv` lists the sample.

## Licence

{lic_text}

## What was changed

Only reading: the text of the table cells was taken from each PDF with pdfplumber, whitespace collapsed. Nothing was corrected or
completed. Added columns: `pdf_url`, `bureau`, `name_cells`, `parse_status`, `parse_note`, `layout`, `record_no`. The cells of the withheld records were set to null (see Known issues).

## Known issues (measured 2026-10-31)

- Not every point has attributes: of the {len(pts):,} points, {int((pts["pdf_match"] == "pdf_unique").sum()):,} have a PDF of their own
  (`pdf_unique`); {int((pts["pdf_match"] == "pdf_shared").sum()):,} share a PDF or the PDF holds several records (`pdf_shared`), {int((pts["pdf_match"] == "pdf_missing").sum())}
  have a PDF that is missing (404) and {int((pts["pdf_match"] == "no_pdf").sum())} have no link. {int((rec["layout"] == "unknown").sum())} PDFs have a layout that the reader does
  not know; all their attributes are null.
- Withheld cells (furigana): some bureaus print the reading (furigana) of the names above the names, and the text of the PDF then runs
  the reading into the name cells, for example `しどう おおだてまつきせん 市道 大館松木線`; the name cannot be told from the reading
  without guessing. In such a record the three cells `place_name`, `underpass_name` and `road_kind` are **null and `name_cells` is
  `withheld_furigana_in_source`** ({nfur} records, {fur_pts} points; by prefecture: {fur_pref}). A record is marked when one of the
  three cells begins with a hiragana run and a space, or holds a hiragana, a space and a hiragana; this can also catch a real name that
  was wrapped, and it can miss a reading that carries no space. The other cells of the record (municipality, address, manager, police,
  fire station) were not affected in the cells that were checked, and are published. The PDF itself (`pdf_url`) has the names.
- The 管理番号 can carry a parse artefact (a lost hyphen as in 茨城県02-001 or 山形県02-204, or a second line appended as in
  兵庫県-02-076西宮-⑥): {nmg:,} of the {len(rok):,} records with `parse_status` ok do not match the pattern 県名-02-nnn. The file stem
  `pdf_key` is the reliable key. In some PDFs the number in the file name differs from the number in the PDF itself (`pdf_key_consistent`
  false), which is as published.
- A PDF can be replaced by the bureau; the sha256 is that of the file fetched on 2026-10-30 and 2026-10-31.
- The layout reader knows A and B; 403 PDFs of other layouts are not read.

## Reproduce

`scripts/07_fetch_pdfs.py` (one request at a time, 2 s pause), `08_parse_pdfs.py`, `09_verify_pdf.py` (`pdftotext -layout` as a
second route), `10_attach.py` (matches the points), `11_build_tables.py` (withholds the furigana cells, adds the URL), `04_card.py`. The scripts of the points dataset
(`01`-`03`, `05`) make the KML table that `10_attach.py` reads; they are in that dataset.
"""
    (ROOT / "data" / "README.md").write_text(card)
    (ROOT / "data" / "LICENSE").write_text(lic_text.replace("**", "") + "\n")
    (ROOT / "data" / "provenance.yaml").write_text(
        "source: MLIT regional bureaus, 道路防災情報Webマップ 箇所表 PDFs (text read; PDFs not redistributed)\n"
        f"fetched: {man['fetched']}\nfiles: {len(man['files'])}\nrows: {len(rec)}\n"
        f"licence_confirmed_bureaus: {','.join(bureaus_in)}\nlicence_basis: site-wide terms of each bureau\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
