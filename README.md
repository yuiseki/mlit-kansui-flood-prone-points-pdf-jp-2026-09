# mlit-kansui-flood-prone-points-pdf-jp-2026-09

Scripts that fetch the 箇所表 PDFs linked from the 冠水想定箇所 KML points of the eight regional bureaus of the MLIT, read their
tables as text, verify the reading, and publish the tables (not the PDFs).

The data and its card are on Hugging Face:
<https://huggingface.co/datasets/yuiseki/mlit-kansui-flood-prone-points-pdf-jp-2026-09>
(published at revision `34e24d0c94dbeec34a45dba934675ec1a1cf0a97`; `docs/revision.json`). The points are a separate dataset:
<https://huggingface.co/datasets/yuiseki/mlit-kansui-flood-prone-points-jp-2026-09>.

- `scripts/07_fetch_pdfs.py`: fetch the PDFs (kept locally only, with sha256), `08_parse_pdfs.py`: read the tables.
- `scripts/09_verify_pdf.py`: look every parsed cell up in `pdftotext -layout` of the same PDF.
- `scripts/10_attach.py`, `11_build_tables.py`: match the points, withhold the cells that run into the furigana, write the tables.
- `scripts/04_card.py`, `src/publish.py`, `scripts/12_verify_hub.py`: the card, the publication, the read-back.

The PDFs are not redistributed. The code is offered as is; the data is under the terms of the bureaus (PDL1.0), see the card.
