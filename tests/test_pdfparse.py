import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import pdfparse

# table rows as pdfplumber returned them for two real 箇所表 PDFs (the PDFs themselves are not kept in the repository)
A_MIE = [
    ["冠水想定箇所 説明表", "", "", "", "", "", "", ""],
    ["管理番号", "箇所名称", "", "", "", "アンダーパス等名称", "", "種別"],
    ["三重県-02-185", "鵜殿熊野線", "", "", "", "―", "", "一般県道"],
    ["住 所", "", "", "", "", "", "", ""],
    ["県名", "", "市町村", "字丁目", "", "番地", "", ""],
    ["三重県", "", "紀宝町", "神内", "", "493付近", "", ""],
    ["管理者", "", "", "警察署", "", "消防署", "", ""],
    ["名称", "熊野建設事務所", "", "名称", "紀宝警察署", "名称", "熊野市消防本部", ""],
    ["TEL", "0597(89)6147", "", "TEL", "0735(33)0110", "TEL", "0597(89)0119", ""],
    ["備考", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", ""],
    ["位置図", "", "", "", "", "", "", ""],
]
A_TOKYO = [
    ["道路冠水想定箇所 箇所表", "", "", "", "", "", ""],
    ["管理番号", "箇所名称", "", "", "アンダーパス等名称", "", "種別"],
    [
        "東京都-02-\n121",
        "特別区道荒298号線(補助第331号線）",
        "",
        "",
        "南千住北架道橋\n(JR常磐線&貨物線下)",
        "",
        "区道",
    ],
    ["住所", "", "", "", "", "", ""],
    ["都道府県名", "市町村", "字丁目", "", "番地", "", ""],
    ["東京都", "荒川区", "南千住4丁目", "", "", "", ""],
    ["管理者", "", "警察署", "", "消防署", "", ""],
    ["名称", "荒川区", "名称", "南千住警察署", "名称", "荒川消防署", ""],
    ["TEL", "03-3802-3111", "TEL", "03-3805-0110", "TEL", "03-3806-0119", ""],
    ["備考", "", "", "", "", "", ""],
    ["", "", "", "", "", "", ""],
    ["位置図", "", "", "", "", "", ""],
]


def test_layout_a_mie_form():
    layout, recs = pdfparse.parse_tables([A_MIE])
    assert layout == "A" and len(recs) == 1
    r = recs[0]
    assert r["mgmt_no"] == "三重県-02-185"
    assert (r["place_name"], r["underpass_name"], r["road_kind"]) == (
        "鵜殿熊野線",
        "―",
        "一般県道",
    )
    assert (r["pref_name"], r["municipality"], r["aza_chome"], r["banchi"]) == (
        "三重県",
        "紀宝町",
        "神内",
        "493付近",
    )
    assert (r["manager_name"], r["police_name"], r["fire_name"]) == (
        "熊野建設事務所",
        "紀宝警察署",
        "熊野市消防本部",
    )
    assert (r["manager_tel"], r["police_tel"], r["fire_tel"]) == (
        "0597(89)6147",
        "0735(33)0110",
        "0597(89)0119",
    )
    assert r["remarks"] is None and r["parse_status"] == "ok"


def test_layout_a_tokyo_form_has_other_column_positions_and_split_cells():
    layout, recs = pdfparse.parse_tables([A_TOKYO])
    r = recs[0]
    assert layout == "A"
    assert r["mgmt_no"] == "東京都-02-121"  # a line break splits the identifier
    assert (
        r["underpass_name"] == "南千住北架道橋 (JR常磐線&貨物線下)"
    )  # whitespace only is changed
    assert r["banchi"] is None  # empty in the PDF: null, not guessed
    assert (r["manager_name"], r["police_name"], r["fire_name"]) == (
        "荒川区",
        "南千住警察署",
        "荒川消防署",
    )
    assert r["parse_status"] == "ok"


def test_unknown_layout_gives_no_rows():
    layout, recs = pdfparse.parse_tables([[["something", "else"]]])
    assert layout == "unknown" and recs == []


def test_missing_required_cell_gives_ambiguous_not_a_guess():
    rows = [list(r) for r in A_MIE]
    rows[7] = ["名称", "", "", "名称", "紀宝警察署", "名称", "熊野市消防本部", ""]
    r = pdfparse.parse_tables([rows])[1][0]
    assert r["manager_name"] is None or r["manager_name"] != "熊野建設事務所"
    assert r["parse_status"] == "ambiguous"


B_TOYAMA = [
    [
        "整理番号",
        "富山県-02-\n044",
        "道路名",
        "国道8号",
        "",
        "施設名",
        "富山市水橋高寺（1）No.30ボックス",
    ],
    ["地 先 名", "", "富山県富山市水橋高寺", "", "", "", ""],
    ["連絡先", "警察署", "", "富山中央警察署 076-444-0110", "", "", ""],
    ["", "消防署", "", "水橋消防署 076-478-0061", "", "", ""],
    [
        "",
        "道路管理者",
        "",
        "富山河川国道事務所\n黒部国道維持出張所",
        "0765-52-1714",
        "",
        "",
    ],
    ["付 近 図", "", "", "", "", "", ""],
]
B_NIIGATA = [
    [
        "整理番号",
        "新潟県-02-\n405",
        "道路名",
        "一般国道 113号",
        "",
        "施設名",
        "（施設名現地表示 有り 無し）",
    ],
    ["地 先 名", "", "新潟市東区浜谷町2丁目3番～物見山3丁目2番", "", "", "", ""],
    [
        "内部用\n連絡先\nリスト",
        "警察署",
        "",
        "新潟東警察署 交通課 TEL 025-279-0110",
        "",
        "",
        "",
    ],
    ["", "消防署", "", "東消防署 消防課 TEL 025-275-9111", "", "", ""],
    [
        "",
        "道路管理者",
        "",
        "新潟市東区役所建設課",
        "① 025-250-2621 （建設課維持係）",
        "",
        "",
    ],
    ["冠水範囲", "周辺一帯", "", "冠水原因", "下水道能力不足・窪地", ""],
    ["1m以上の冠水の有無", "", "無", "排水ポンプの有無", "", "無"],
]


def test_layout_b_toyama_form():
    layout, recs = pdfparse.parse_tables([B_TOYAMA])
    r = recs[0]
    assert layout == "B" and r["parse_status"] == "ok"
    assert r["mgmt_no"] == "富山県-02-044" and r["road_name"] == "国道8号"
    assert (
        r["underpass_name"] == "富山市水橋高寺（1）No.30ボックス"
        and r["sakimei"] == "富山県富山市水橋高寺"
    )
    assert (
        r["police_text"] == "富山中央警察署 076-444-0110"
    )  # name and TEL together, as published
    assert (
        r["manager_name"] == "富山河川国道事務所 黒部国道維持出張所"
        and r["manager_tel_text"] == "0765-52-1714"
    )


def test_layout_b_niigata_form_keeps_the_extra_items():
    r = pdfparse.parse_tables([B_NIIGATA])[1][0]
    assert r["mgmt_no"] == "新潟県-02-405"
    assert (
        r["extra_cells"]["冠水範囲"] == "周辺一帯"
        and r["extra_cells"]["冠水原因"] == "下水道能力不足・窪地"
    )
    assert (
        r["extra_cells"]["1m以上の冠水の有無"] == "無"
        and r["extra_cells"]["排水ポンプの有無"] == "無"
    )
    assert r["parse_status"] == "ok"


def test_unreadable_glyphs_become_null_and_ambiguous():
    rows = [list(r) for r in A_MIE]
    rows[2][1] = "(cid:16089)(cid:16076)(cid:18103)"
    r = pdfparse.parse_tables([rows])[1][0]
    assert r["place_name"] is None
    assert r["parse_status"] == "ambiguous" and "place_name" in r["parse_note"]
    assert r["mgmt_no"] == "三重県-02-185"  # the other cells stay
