import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import kansui

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))


def test_kml_url_uses_https_and_kml_dir():
    base = "http://www.thr.mlit.go.jp/road/doro_bosaijoho_webmap"
    assert kansui.kml_url(base, "02_aomori_kansui_point") == (
        "https://www.thr.mlit.go.jp/road/doro_bosaijoho_webmap/kml/02_aomori_kansui_point.kml"
    )


def test_parse_bases():
    assert kansui.parse_bases("a b\nc d\n") == {"a": "b", "c": "d"}


@pytest.mark.parametrize(
    "base,bureau",
    [
        ("https://www.ktr.mlit.go.jp/honkyoku/road/x", "ktr"),
        ("https://www.qsr.mlit.go.jp/n-michi/x", "qsr"),
    ],
)
def test_bureau_of(base, bureau):
    assert kansui.bureau_of(base) == bureau


def test_layer_parts():
    assert kansui.layer_parts("12_chiba_kansui_point") == ("12", "chiba")
    with pytest.raises(ValueError):
        kansui.layer_parts("chiba")


KML = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2"><Document>
<!-- A-02-001 -->
<Placemark><name> 青森市 </name><description><![CDATA[<table><tr><td>箇所表</td><td><a href="../attachment/aomoriken-02-201.pdf" target="_blank">x</a></td></tr></table>]]></description>
<styleUrl>#S</styleUrl><Point><coordinates>140.81735,40.846249</coordinates></Point></Placemark>
<!-- A-02-002 2019/05/29 deleted
<Placemark><name>gone</name><Point><coordinates>1,2</coordinates></Point></Placemark> -->
<Placemark><name>b</name><description><![CDATA[<a href="https://x.example/attachment/b-02-1.pdf">p</a>]]></description>
<styleUrl>#S</styleUrl><Point><coordinates>141.0,41.0,0</coordinates></Point></Placemark>
</Document></kml>"""


def test_parse_kml_reads_only_live_placemarks():
    import export

    rows, withdrawn = export.parse_kml(
        KML, "https://www.thr.mlit.go.jp/road/doro_bosaijoho_webmap"
    )
    assert [r["name"] for r in rows] == ["青森市", "b"]
    assert withdrawn == 1
    assert rows[0]["lon"] == 140.81735 and rows[0]["lat"] == 40.846249
    assert rows[0]["pdf_href"] == "../attachment/aomoriken-02-201.pdf"
    assert (
        rows[0]["pdf_url"]
        == "https://www.thr.mlit.go.jp/road/doro_bosaijoho_webmap/attachment/aomoriken-02-201.pdf"
    )
    assert rows[0]["pdf_key"] == "aomoriken-02-201"
    assert rows[1]["pdf_url"] == "https://x.example/attachment/b-02-1.pdf"
    assert rows[1]["lon"] == 141.0 and rows[1]["lat"] == 41.0


def _publish():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "publish", Path(__file__).parents[1] / "src" / "publish.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_licence_gate_needs_every_bureau_in_the_table_confirmed():
    pub = _publish()
    man = {"a": {"bureau": "kkr"}, "b": {"bureau": "ktr"}}
    card = "license_name: pdl-1.0"
    st = {"kkr": {"confirmed": True}, "ktr": {"confirmed": True}}
    assert pub.licence_ok(st, man, ["a", "b"], card)
    assert not pub.licence_ok(
        {"kkr": {"confirmed": True}, "ktr": {"confirmed": False}}, man, ["a", "b"], card
    )
    assert pub.licence_ok(
        {"kkr": {"confirmed": True}, "ktr": {"confirmed": False}}, man, ["a"], card
    )  # b is not in the table
    assert not pub.licence_ok(st, man, ["a", "b"], "license_name: unconfirmed")
    assert not pub.licence_ok(
        {}, man, ["a"], card
    )  # a bureau with no status is not confirmed


def test_extract_terms_quotes_the_use_paragraph_and_the_important_notes():
    import terms

    text = (
        "リンクについて 原則リンクフリーです。 2.当ホームページのコンテンツの利用について "
        "当ホームページで公開している情報（以下「コンテンツ」といいます。）の著作権は、特記されていない限り国土交通省X地方整備局に帰属し、"
        "権利表記の記載がない限り「 公共データ利用規約（第1.0版） 」（PDL1.0）に準拠した利用条件の下で、利用することができます。 "
        "PDL1.0のうち、重要情報については「PDL1.0に関する重要情報」を参照してください。 "
        "PDL1.0に関する重要情報 １） 出典の記載について ア） （出典記載例）出典：X地方整備局ホームページ （当該ページのURL） "
        "イ） 加工して作成 ２） 本利用ルールが適用されないコンテンツについて ア） ロゴ イ） 別の利用ルール ぺージの上部へ フッター"
    )
    r = terms.extract_terms(text)
    assert r["use_sentence"].startswith("当ホームページで公開している情報")
    assert r["use_sentence"].endswith("利用することができます。")
    assert "PDL1.0" in r["use_sentence"]
    assert r["important"].startswith("PDL1.0に関する重要情報 １）")
    assert r["important"].endswith("別の利用ルール")
    assert "フッター" not in r["important"]


def test_extract_terms_for_the_tohoku_form():
    import terms

    text = "２． 当ホームページのコンテンツの利用について 当ホームページのコンテンツの利用については、【 公共データ利用規約（第 1.0 版） (digital.go.jp) ［デジタル庁］】に定めるとおりです。 ３． プライバシーポリシー"
    r = terms.extract_terms(text)
    assert r["use_sentence"].endswith("に定めるとおりです。")
    assert "公共データ利用規約" in r["use_sentence"]
    assert r["important"] is None


def test_pdf_plan_dedupes_and_sorts():
    urls = [
        "https://www.a.mlit.go.jp/x/b.pdf",
        None,
        "https://www.a.mlit.go.jp/x/a.pdf",
        "https://www.a.mlit.go.jp/x/b.pdf",
        float("nan"),
    ]
    assert kansui.pdf_plan(urls) == [
        "https://www.a.mlit.go.jp/x/a.pdf",
        "https://www.a.mlit.go.jp/x/b.pdf",
    ]


def test_pdf_name_keeps_the_bureau_apart():
    assert (
        kansui.pdf_name(
            "https://www.ktr.mlit.go.jp/honkyoku/road/doro_bosaijoho_webmap/attachment/chibaken-02-001.pdf"
        )
        == "ktr__chibaken-02-001.pdf"
    )
    with pytest.raises(ValueError):
        kansui.pdf_name("https://example.com/a.txt")
