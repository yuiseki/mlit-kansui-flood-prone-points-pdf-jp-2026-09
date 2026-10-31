# Licence findings (2026-10-30)

Question: is the KML of 冠水想定箇所 under the Public Data License 1.0 (PDL1.0)?

## First pass (superseded)

The Webmap pages (top, map, list, scripts) of the eight bureaus carry no licence or terms statement (searched for 利用規約, 公共データ,
ライセンス, 二次利用, 著作権, オープンデータ), and two web searches did not find one. Saved under `evidence/pages/`.

## Second pass: each bureau's own terms page (footer link 'リンク・著作権等について' and the like), raw HTML saved under `evidence/terms/`

All eight bureaus' pages say that the content is usable under PDL1.0 (quotations in `docs/bureau_terms.json`, produced by
`scripts/00_terms.py` from the saved pages):

| Bureau | Page | Form of the statement |
|---|---|---|
| 東北 thr | https://www.thr.mlit.go.jp/policy.pdf (a PDF linked from the top page footer) | 「当ホームページのコンテンツの利用については、公共データ利用規約（第1.0版）に定めるとおりです。」 (no 重要情報 block, no attribution example) |
| 関東 ktr | https://www.ktr.mlit.go.jp/guide/copyright.html | PDL1.0 sentence with 重要事項 |
| 北陸 hrr | https://www.hrr.mlit.go.jp/help.html | PDL1.0 sentence with 重要情報 |
| 中部 cbr | https://www.cbr.mlit.go.jp/policy.htm | PDL1.0 sentence with 重要情報 |
| 近畿 kkr | https://www.kkr.mlit.go.jp/link.html | PDL1.0 sentence with 重要情報 |
| 四国 skr | https://www.skr.mlit.go.jp/manual.html | PDL1.0 sentence with 重要情報 |
| 九州 qsr | https://www.qsr.mlit.go.jp/pp/index.html | PDL1.0 sentence with 重要事項 (adds: content restricted by individual laws) |
| 中国 cgr | https://www.cgr.mlit.go.jp/about_manual/index.html | PDL1.0 sentence with 重要情報 |

Decision: all eight bureaus are included; none is excluded. The basis is each bureau's site-wide terms; no data-specific
notice exists on the Webmap pages or in the KML (card says so).

## Overrides checked

- KML: no text outside the Placemarks and Styles (no Document name or description, no atom link), no rights word in any
  Placemark description (the description is only the link to the 箇所表 PDF). The icon style URLs point to GSI symbols
  (not part of the data).
- Webmap pages: the top pages of the eight bureaus and the map pages of all eight: no 特記 or rights notice; the only mention is
  that the background map is the GSI's 地理院地図.
- 箇所表 PDFs (40 looked at, none uploaded): 2 say 'この地図は、国土地理院の標準地図を使用しています'; the position maps carry a GSI
  map mark and the sites have street photographs; no other rights mark in the text; 366 embedded images (not inspected one by one).
  The PDFs are therefore not part of the dataset (sha256 only).

## Other regions

北海道 and 沖縄県: no KML of the same kind found. 中国地方整備局: found and added (5 KML).
