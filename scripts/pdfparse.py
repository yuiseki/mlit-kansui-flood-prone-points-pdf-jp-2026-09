"""Parse the tables of the 箇所表 PDFs (a module, so that the tests can import it).

Every cell is kept as published; only whitespace is collapsed. A value that cannot be read with certainty is left
null and the row gets a parse_status other than ok.
"""

import re

LABELS_A = {
    "管理番号",
    "箇所名称",
    "アンダーパス等名称",
    "種別",
    "都道府県名",
    "県名",
    "市町村",
    "字丁目",
    "番地",
}
TITLES_A = ("冠水想定箇所 説明表", "道路冠水想定箇所 箇所表")


def clean(cell) -> str | None:
    """Collapse whitespace (a line break inside a cell is layout); None for an empty cell."""
    if cell is None:
        return None
    s = re.sub(r"\s+", " ", str(cell)).strip()
    return s or None


def compact(cell) -> str | None:
    """For an identifier (the management number), which a line break may split: remove all whitespace."""
    s = clean(cell)
    return re.sub(r"\s+", "", s) if s else None


def rows_of(tables) -> list[list]:
    return [list(r) for t in tables for r in t]


def classify(rows: list[list]) -> str:
    firsts = [clean(r[0]) for r in rows if r]
    flat = {clean(c) for r in rows for c in r}
    if (
        "管理番号" in firsts
        and "管理者" in flat
        and ("住所" in flat or "住 所" in flat)
    ):
        return "A"
    if "整理番号" in firsts and any(
        f and "地 先 名" in f or f == "地先名" for f in firsts
    ):
        return "B"
    return "unknown"


def _aligned(header: list, values: list) -> dict[str, str | None]:
    return {
        clean(h): clean(values[i]) if i < len(values) else None
        for i, h in enumerate(header)
        if clean(h)
    }


def _pairs(row: list, labels=("名称", "TEL")) -> list[str | None]:
    """The values that follow the 名称 / TEL labels of a row, in order; None when a label has no value."""
    out, cells = [], [clean(c) for c in row]
    i = 0
    while i < len(cells):
        if cells[i] in labels:
            j = i + 1
            while j < len(cells) and cells[j] is None:
                j += 1
            if j < len(cells) and cells[j] not in labels:
                out.append(cells[j])
                i = j + 1
                continue
            out.append(None)
        i += 1
    return out


def parse_a(rows: list[list]) -> dict:
    rec: dict = {}
    idx = {clean(r[0]): n for n, r in enumerate(rows) if r and clean(r[0])}
    if "管理番号" in idx:
        n = idx["管理番号"]
        d = _aligned(rows[n], rows[n + 1])
        rec["mgmt_no"] = compact(rows[n + 1][0]) if rows[n + 1] else None
        rec["place_name"] = d.get("箇所名称")
        rec["underpass_name"] = d.get("アンダーパス等名称")
        rec["road_kind"] = d.get("種別")
    for key in ("都道府県名", "県名"):
        if key in idx:
            n = idx[key]
            d = _aligned(rows[n], rows[n + 1])
            rec["pref_name"], rec["municipality"] = d.get(key), d.get("市町村")
            rec["aza_chome"], rec["banchi"] = d.get("字丁目"), d.get("番地")
    if "管理者" in idx:
        n = idx["管理者"]
        names = _pairs(rows[n + 1], ("名称",))
        tels = _pairs(rows[n + 2], ("TEL",)) if n + 2 < len(rows) else []
        for k, who in enumerate(("manager", "police", "fire")):
            rec[f"{who}_name"] = names[k] if k < len(names) else None
            rec[f"{who}_tel"] = tels[k] if k < len(tels) else None
    if "備考" in idx:
        n = idx["備考"]
        txt = []
        for r in rows[n + 1 :]:
            if r and clean(r[0]) in ("位置図",):
                break
            txt += [c for c in (clean(c) for c in r) if c]
        rec["remarks"] = " ".join(txt) or None
    return rec


A_REQUIRED = ("mgmt_no", "place_name", "pref_name", "municipality", "manager_name")


def status_a(rec: dict) -> str:
    return "ok" if all(rec.get(k) for k in A_REQUIRED) else "ambiguous"


def mark_unreadable(rec: dict) -> dict:
    """A cell whose glyphs the PDF does not map to text (pdfplumber shows (cid:NNNN)) is not readable: null and noted."""
    bad = [k for k, v in rec.items() if isinstance(v, str) and "(cid:" in v]
    for k in bad:
        rec[k] = None
    if bad:
        rec["parse_note"] = "unreadable glyphs in: " + ", ".join(bad)
        rec["parse_status"] = "ambiguous"
    return rec


def parse_tables(tables) -> tuple[str, list[dict]]:
    rows = rows_of(tables)
    layout = classify(rows)
    if layout == "A":
        rec = parse_a(rows)
        rec["parse_status"] = status_a(rec)
        return "A", [mark_unreadable(rec)]
    if layout == "B":
        rec = parse_b(rows)
        rec["parse_status"] = status_b(rec)
        return "B", [mark_unreadable(rec)]
    return layout, []


B_PAIR_LABELS = ("整理番号", "道路名", "施設名")
B_EXTRA_LABELS = (
    "冠水範囲",
    "冠水原因",
    "1m以上の冠水の有無",
    "排水ポンプの有無",
    "情報入手方法",
    "通行止方法",
    "看板に記載する連絡先",
    "注意喚起方法",
    "その他",
)


def _after(cells: list, i: int, stop: set) -> list[str]:
    """The non-empty cells that follow position i up to the next label."""
    out = []
    for c in cells[i + 1 :]:
        if c in stop:
            break
        if c:
            out.append(c)
    return out


def parse_b(rows: list[list]) -> dict:
    rec: dict = {}
    stop = set(B_PAIR_LABELS) | {"地先名", "警察署", "消防署", "道路管理者"}
    extras: dict = {}
    for r in rows:
        cells = [clean(c) for c in r]
        flat = [c.replace(" ", "") if c else c for c in cells]
        for i, c in enumerate(flat):
            if c == "整理番号":
                v = _after(cells, i, stop)
                rec["mgmt_no"] = compact(v[0]) if v else None
            elif c == "道路名":
                v = _after(cells, i, stop)
                rec["road_name"] = v[0] if v else None
            elif c == "施設名":
                v = _after(cells, i, stop)
                rec["underpass_name"] = " ".join(v) if v else None
            elif c == "地先名":
                v = _after(cells, i, stop)
                rec["sakimei"] = " ".join(v) if v else None
            elif c in ("警察署", "消防署"):
                v = _after(cells, i, stop)
                rec["police_text" if c == "警察署" else "fire_text"] = (
                    " ".join(v) if v else None
                )
            elif c == "道路管理者":
                v = _after(cells, i, stop)
                rec["manager_name"] = v[0] if v else None
                rec["manager_tel_text"] = " ".join(v[1:]) or None
        # the extra items of some forms: label cell then its value cells (a label may be followed by a second pair)
        for i, c in enumerate(flat):
            if c in B_EXTRA_LABELS and c not in extras:
                nxt = [x for x in cells[i + 1 :] if x]
                extras[c] = (
                    nxt[0]
                    if nxt and flat[cells.index(nxt[0], i + 1)] not in B_EXTRA_LABELS
                    else None
                )
    rec["extra_cells"] = extras or None
    return rec


B_REQUIRED = ("mgmt_no", "road_name", "sakimei")


def status_b(rec: dict) -> str:
    return (
        "ok"
        if all(rec.get(k) for k in B_REQUIRED)
        and (rec.get("police_text") or rec.get("fire_text"))
        else "ambiguous"
    )
