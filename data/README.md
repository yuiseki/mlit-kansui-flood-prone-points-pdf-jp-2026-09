---
license: other
license_name: pdl-1.0
license_link: https://www.digital.go.jp/resources/open_data/public_data_license_v1.0
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

# mlit-kansui-flood-prone-points-pdf-jp-2026-09

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

The PDF of each point is linked from its KML Placemark (`pdf_url` of the points dataset). 4,429 unique PDFs are linked (some by several points). They were fetched on 2026-10-30 and 2026-10-31
(`fetched_all` of `PDF_MANIFEST.json`), one request at a time with a 2 s pause; 18 of them are missing (HTTP 404).
The KML files are described in the points dataset.

## Files

| File | Rows | What a row is |
|---|---|---|
| `parquet/pdf_records.parquet` | 4,410 | A PDF that was read (one record each); the cells as read |
| `parquet/point_pdf.parquet` | 4,525 | A KML point: the key of its PDF and how it was matched |
| `raw/*/PDF_MANIFEST.json` | 4,429 | A PDF: URL, status, size, Last-Modified, sha256 |

`pdf_records`: `pdf_name` (the file name used locally, `<bureau>__<stem>.pdf`), `pdf_key` (the stem; the key of the points
dataset), `pdf_sha256`, `pdf_pages`, `layout`, `record_no`, `mgmt_no` (管理番号/整理番号), `place_name` (箇所名称), `road_name` (道路名),
`underpass_name` (アンダーパス等名称/施設名), `road_kind` (種別), `pref_name`, `municipality` (市町村), `aza_chome` (字丁目), `banchi`
(番地), `sakimei` (地先名), `manager_name`/`manager_tel` (管理者), `manager_tel_text`, `police_name`/`police_tel`/`police_text`,
`fire_name`/`fire_tel`/`fire_text`, `remarks` (備考), `extra_cells` (JSON: the extra items of some forms, 冠水範囲, 冠水原因, 排水ポンプの有無 ...),
`parse_note`, `parse_status`, `bureau`, `name_cells_have_furigana`. In layout B the police and fire cells hold name and TEL together as
published (`*_text`), and the manager's further cells are in `manager_tel_text`.

`point_pdf`: `fid`, `layer`, `pref`, `name`, `pdf_name`, `pdf_key`, `pdf_match`, `pdf_key_consistent`.

## How it was read

The tables were read with pdfplumber, **the text of every cell as published (only whitespace collapsed)**. A cell that could not be
read with certainty is null; nothing was guessed, and no language model was used. `scripts/08_parse_pdfs.py` is the reader and
`tests/test_pdfparse.py` its tests.

| layout / parse_status | PDFs (records) |
|---|---|
| A/ambiguous | 54 |
| A/ok | 3315 |
| B/ok | 638 |
| unknown/layout_unknown | 403 |

`parse_status`: `ok` (all required cells read), `ambiguous` (a required cell is empty or unreadable; see `parse_note`),
`layout_unknown` (no known layout; all attributes null). Layout A: the 説明表 / 箇所表 / 様式 tables; layout B: the
道路冠水(危険)想定箇所 forms (石川, 富山, 新潟).

How the points are matched to the table (`pdf_match`; the key is the PDF file linked in the KML):

| pdf_match | points |
|---|---|
| pdf_unique | 3997 |
| pdf_shared | 504 |
| pdf_missing | 20 |
| no_pdf | 4 |

`pdf_unique`: the PDF is linked by this point only and holds one record, so its record is the point's; `pdf_shared`: the PDF is linked
by several points or holds several records, and it is not said which record is which point; `no_pdf`; `pdf_missing`.
`pdf_key_consistent` compares the number in the file name with the number in the management number (a check only; false for 119
points that have a record).

Checks: 48,211 parsed cells of 4007 PDFs were looked up in `pdftotext -layout` of the same PDF
(218 not found, all management numbers that the PDF breaks over two lines; the count of 管理番号/整理番号
labels equals the record count except 6 PDFs). Manual check: 30 points drawn at random (seed
20261030) were compared with the text of their PDFs: 28 of 30 had every cell matching the PDF text
(every published cell matched the text of the PDF; the 28 include 4 points (熊本県 2, 宮崎県, 鹿児島県) whose name cells ran together with the furigana and are therefore withheld in `joined`; in the other 2 the 管理番号 cell carries a parse artefact: a hyphen lost in 茨城県02-019 and 兵庫県-02-076西宮-⑥ with the second line appended). `docs/manual_check_sample.tsv` lists the sample.

## Licence

Each bureau's own site-wide terms say that its content is usable under the Public Data License 1.0
(公共データ利用規約 第1.0版, PDL1.0; compatible with CC BY 4.0), unless a right notice says otherwise. **The basis is the
bureaus' site-wide terms. No licence notice specific to the Webmap pages or the KML files exists** (the Webmap pages,
their scripts and the KML carry no rights notice: checked 2026-10-30). Judge for yourself whether the site-wide
terms reach these files. The pages were saved under `evidence/terms/`; the quotations are in `docs/bureau_terms.json`.

The Kinki (近畿) sentence, from <https://www.kkr.mlit.go.jp/link.html>:

> 当ホームページで公開している情報（以下「コンテンツ」といいます。）の著作権は、特記されていない限り国土交通省近畿地方整備局に帰属し、権利表記の記載がない限り「 公共データ利用規約（第1.0版） 」（PDL1.0）に準拠した利用条件の下で、利用することができます。

The sentence of each bureau whose points are in this dataset:

- 中部地方整備局 (https://www.cbr.mlit.go.jp/policy.htm):
  > 当ホームページで公開している情報（以下「コンテンツ」といいます。）の著作権は、特記されていない限り国土交通省中部地方整備局に帰属し、権利表記の記載がない限り「 公共データ利用規約（第1.0版） 」（PDL1.0）に準拠した利用条件の下で、利用することができます。
- 中国地方整備局 (https://www.cgr.mlit.go.jp/about_manual/index.html):
  > 当ホームページで公開している情報（以下「コンテンツ」といいます。）の著作権は、特記されていない限り国土交通省中国地方整備局に帰属し、権利表記の記載がない限り「 公共データ利用規約（第1.0版） 」（PDL1.0）に準拠した利用条件の下で、利用することができます。
- 北陸地方整備局 (https://www.hrr.mlit.go.jp/help.html):
  > 当ホームページで公開している情報（以下「コンテンツ」といいます。）の著作権は、特記されていない限り国土交通省北陸地方整備局に帰属し、権利表記の記載がない限り【 公共データ利用規約（第1.0版）（digital.go.jp）［デジタル庁］ 】（以下「PDL1.0」といいます。）に準拠した利用条件の下で、利用することができます。
- 近畿地方整備局 (https://www.kkr.mlit.go.jp/link.html):
  > 当ホームページで公開している情報（以下「コンテンツ」といいます。）の著作権は、特記されていない限り国土交通省近畿地方整備局に帰属し、権利表記の記載がない限り「 公共データ利用規約（第1.0版） 」（PDL1.0）に準拠した利用条件の下で、利用することができます。
- 関東地方整備局 (https://www.ktr.mlit.go.jp/guide/copyright.html):
  > 関東地方整備局ウェブサイトで掲載・発信している情報(以下「コンテンツ」といいます。)の著作権は、特記されていない限り関東地方整備局に帰属し、権利表記の記載がない限り「公共データ利用規約(第1.0版)」(PDL1.0)に準拠した利用条件の下で、利用することができます。
- 九州地方整備局 (https://www.qsr.mlit.go.jp/pp/index.html):
  > 国土交通省九州地方整備局ウェブサイトで掲載・発信している情報（以下「コンテンツ」といいます。）の著作権は、特記されていない限り国土交通省九州地方整備局に帰属し、権利表記の記載がない限り「 公共データ利用規約（第1.0版） 」（PDL1.0）に準拠した利用条件の下で、利用することができます。
- 四国地方整備局 (https://www.skr.mlit.go.jp/manual.html):
  > 当ホームページで公開している情報（以下「コンテンツ」といいます。）の著作権は、特記されていない限り国土交通省四国地方整備局に帰属し、権利表記の記載がない限り「 公共データ利用規約（第1.0版） 」（PDL1.0）に準拠した利用条件の下で、利用することができます。
- 東北地方整備局 (https://www.thr.mlit.go.jp/policy.pdf):
  > 当ホームページのコンテンツの利用については、【 公共データ利用規約（第 1.0 版） (digital.go.jp) ［デジタル庁］】に定めるとおりです。

The terms exclude symbol marks, logos and character designs, and content for which a separate rule is stated
(the Kyushu page adds that some content may be restricted by individual laws). The background map of the Webmaps is
the GSI's 地理院地図 and is not part of the data. The 箇所表 PDFs (not included here) hold GSI maps and photographs of
the sites; no rights mark other than the GSI map note was found on the 40 PDFs that were looked at.

Attribution, per bureau (出典：<局>ホームページ（URL）):

- 中部地方整備局: 出典：中部地方整備局ホームページ（https://www.cbr.mlit.go.jp/road_map/doro_bosaijoho_webmap/main/index.html）
- 中国地方整備局: 出典：中国地方整備局ホームページ（https://www.cgr.mlit.go.jp/doro_bosaijoho_webmap/main/index.html）
- 北陸地方整備局: 出典：北陸地方整備局ホームページ（https://www.hrr.mlit.go.jp/road/doro_bousaijoho_webmap/main/index.html）
- 近畿地方整備局: 出典：近畿地方整備局ホームページ（https://www.kkr.mlit.go.jp/road/doro_bosaijoho_webmap/main/index.html）
- 関東地方整備局: 出典：関東地方整備局ホームページ（https://www.ktr.mlit.go.jp/honkyoku/road/doro_bosaijoho_webmap/main/index.html）
- 九州地方整備局: 出典：九州地方整備局ホームページ（https://www.qsr.mlit.go.jp/n-michi/doro_bosaijoho_webmap/main/index.html）
- 四国地方整備局: 出典：四国地方整備局ホームページ（https://www.skr.mlit.go.jp/road/doro_bosaijoho_webmap/main/index.html）
- 東北地方整備局: 出典：東北地方整備局ホームページ（https://www.thr.mlit.go.jp/road/doro_bosaijoho_webmap/main/index.html）

Processing notice (編集・加工等を行ったことの記載。国が作成したかのような態様で公表・利用してはいけません):

- 中部地方整備局: 「道路防災情報Webマップ 冠水想定箇所」（中部地方整備局）（https://www.cbr.mlit.go.jp/road_map/doro_bosaijoho_webmap/main/index.html）を加工して作成
- 中国地方整備局: 「道路防災情報Webマップ 冠水想定箇所」（中国地方整備局）（https://www.cgr.mlit.go.jp/doro_bosaijoho_webmap/main/index.html）を加工して作成
- 北陸地方整備局: 「道路防災情報Webマップ 冠水想定箇所」（北陸地方整備局）（https://www.hrr.mlit.go.jp/road/doro_bousaijoho_webmap/main/index.html）を加工して作成
- 近畿地方整備局: 「道路防災情報Webマップ 冠水想定箇所」（近畿地方整備局）（https://www.kkr.mlit.go.jp/road/doro_bosaijoho_webmap/main/index.html）を加工して作成
- 関東地方整備局: 「道路防災情報Webマップ 冠水想定箇所」（関東地方整備局）（https://www.ktr.mlit.go.jp/honkyoku/road/doro_bosaijoho_webmap/main/index.html）を加工して作成
- 九州地方整備局: 「道路防災情報Webマップ 冠水想定箇所」（九州地方整備局）（https://www.qsr.mlit.go.jp/n-michi/doro_bosaijoho_webmap/main/index.html）を加工して作成
- 四国地方整備局: 「道路防災情報Webマップ 冠水想定箇所」（四国地方整備局）（https://www.skr.mlit.go.jp/road/doro_bosaijoho_webmap/main/index.html）を加工して作成
- 東北地方整備局: 「道路防災情報Webマップ 冠水想定箇所」（東北地方整備局）（https://www.thr.mlit.go.jp/road/doro_bosaijoho_webmap/main/index.html）を加工して作成

This dataset is made by yuiseki from the bureaus' PDFs: their tables were read as text and written as Parquet; the text of the
PDFs is kept as read. It was made by processing the bureaus' data and is not made or endorsed by the State. The licence basis is the
bureaus' site-wide terms, as for the KML; no rights notice specific to the PDFs was found other than the GSI map note (checked on 40 of
them), and the PDFs are not redistributed.


## What was changed

Only reading: the text of the table cells was taken from each PDF with pdfplumber, whitespace collapsed. Nothing was corrected or
completed. Added columns: `bureau`, `name_cells_have_furigana`, `parse_status`, `parse_note`, `layout`, `record_no`.

## Known issues (measured 2026-10-30)

- Not every point has attributes: of the 4,525 points, 3,997 have a PDF of their own
  (`pdf_unique`); 504 share a PDF or the PDF holds several records (`pdf_shared`), 20
  have a PDF that is missing (404) and 4 have no link. 403 PDFs have a layout that the reader does
  not know; all their attributes are null.
- Furigana: some bureaus print the reading of the names above the names, and the text of the PDF then runs the reading into the
  name cells (`place_name`, `underpass_name`, `road_kind`), for example `しどう おおだてまつきせん 市道 大館松木線`.
  `name_cells_have_furigana` is true for 469 records (556 points; by prefecture {'熊本県': 150, '福岡県': 138, '秋田県': 72, '山形県': 69, '鹿児島県': 50, '大分県': 31, '宮崎県': 20, '長崎県': 16, '佐賀県': 6, '青森県': 1, '宮城県': 1, '千葉県': 1, '兵庫県': 1}); the flag marks a cell that begins
  with a hiragana run and a space, or holds a hiragana, a space and a hiragana, and can also mark a real name that was wrapped.
  Cells with furigana are not corrected. A reading that does not carry a space (as in `かわまたせん 川又線`, which is caught, or
  furigana joined to the name without a space, which is not) may be missed.
- The 管理番号 can carry a parse artefact (a lost hyphen as in 茨城県02-001 or 山形県02-204, or a second line appended as in
  兵庫県-02-076西宮-⑥): 219 of the 3,953 records with `parse_status` ok do not match the pattern 県名-02-nnn. The file stem
  `pdf_key` is the reliable key. In some PDFs the number in the file name differs from the number in the PDF itself (`pdf_key_consistent`
  false), which is as published.
- The first reading of 4,410 PDFs did not cover the 18 that are 404. A PDF can be replaced by the bureau; the sha256 is that of the file
  fetched on 2026-10-30 and 2026-10-31.
- The layout reader knows A and B; 403 PDFs of other layouts are not read.

## Reproduce

`scripts/07_fetch_pdfs.py` (one request at a time, 2 s pause), `08_parse_pdfs.py`, `09_verify_pdf.py` (`pdftotext -layout` as a
second route), `10_attach.py` (matches the points), `11_build_tables.py`, `04_card.py`. The scripts of the points dataset
(`01`-`03`, `05`) make the KML table that `10_attach.py` reads; they are in that dataset.
