#!/usr/bin/env python3
"""Read the 45 KML files with an XML parser and write GeoParquet (points, EPSG:4326 as given).

uv run python scripts/02_export_parquet.py    # data/parquet/kansui_points.parquet, docs/export_log.json
"""

import json

import export
import geopandas as gpd
import kansui
import pandas as pd

ROOT = kansui.root()
PREF_JA = {
    "aomori": "青森県", "iwate": "岩手県", "miyagi": "宮城県", "akita": "秋田県", "yamagata": "山形県",
    "fukushima": "福島県", "ibaraki": "茨城県", "tochigi": "栃木県", "gunma": "群馬県", "saitama": "埼玉県",
    "chiba": "千葉県", "tokyo": "東京都", "kanagawa": "神奈川県", "niigata": "新潟県", "toyama": "富山県",
    "ishikawa": "石川県", "fukui": "福井県", "yamanashi": "山梨県", "nagano": "長野県", "gifu": "岐阜県",
    "shizuoka": "静岡県", "aichi": "愛知県", "mie": "三重県", "shiga": "滋賀県", "kyoto": "京都府",
    "osaka": "大阪府", "hyogo": "兵庫県", "nara": "奈良県", "wakayama": "和歌山県", "tokushima": "徳島県",
    "kagawa": "香川県", "ehime": "愛媛県", "kochi": "高知県", "fukuoka": "福岡県", "saga": "佐賀県",
    "nagasaki": "長崎県", "kumamoto": "熊本県", "oita": "大分県", "miyazaki": "宮崎県", "kagoshima": "鹿児島県",
    "tottori": "鳥取県", "shimane": "島根県", "okayama": "岡山県", "hiroshima": "広島県", "yamaguchi": "山口県",
}  # fmt: skip
BUREAU_JA = {"thr": "東北地方整備局", "ktr": "関東地方整備局", "hrr": "北陸地方整備局", "cbr": "中部地方整備局",
             "kkr": "近畿地方整備局", "skr": "四国地方整備局", "qsr": "九州地方整備局", "cgr": "中国地方整備局"}  # fmt: skip


def main() -> int:
    run = max((ROOT / "data" / "raw").glob("*/MANIFEST.json")).parent
    man = json.loads((run / "MANIFEST.json").read_text())
    bases = kansui.parse_bases(
        (ROOT / "data" / "bases_from_user.txt").read_text()
        + (ROOT / "data" / "bases_added.txt").read_text()
    )
    status = json.loads((ROOT / "docs" / "licence_status.json").read_text())["bureaus"]
    frames, log = [], {"run": run.name, "files": {}, "excluded_unconfirmed": {}}
    for layer, m in man["files"].items():
        if not status[m["bureau"]]["confirmed"]:
            log["excluded_unconfirmed"][layer] = m["bureau"]
            continue
        rows, withdrawn = export.parse_kml(
            (run / "kml" / f"{layer}.kml").read_text(encoding="utf-8"), bases[layer]
        )
        code, rom = kansui.layer_parts(layer)
        df = pd.DataFrame(rows)
        df.insert(0, "layer", layer)
        df.insert(1, "pref_code", code)
        df.insert(2, "pref_roma", rom)
        df.insert(3, "pref", PREF_JA[rom])
        df.insert(4, "bureau", m["bureau"])
        df.insert(5, "bureau_ja", BUREAU_JA[m["bureau"]])
        df["source_last_modified"] = m["last_modified"]
        df["source_url"] = m["url"]
        frames.append(df)
        log["files"][layer] = {
            "placemarks": len(rows),
            "withdrawn_commented_out": withdrawn,
        }
    df = pd.concat(frames, ignore_index=True)
    df.insert(0, "fid", range(1, len(df) + 1))
    gdf = gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df["lon"], df["lat"]), crs=4326
    )
    out = ROOT / "data" / "parquet"
    out.mkdir(parents=True, exist_ok=True)
    gdf.to_parquet(
        out / "kansui_points.parquet",
        compression="zstd",
        write_covering_bbox=True,
        index=False,
    )
    log["rows"] = len(gdf)
    log["withdrawn_total"] = sum(
        v["withdrawn_commented_out"] for v in log["files"].values()
    )
    log["rows_without_pdf"] = int(gdf["pdf_url"].isna().sum())
    log["pdf_key_duplicates"] = int(gdf["pdf_key"].dropna().duplicated().sum())
    log["name_duplicates_within_layer"] = int(gdf.duplicated(["layer", "name"]).sum())
    log["coordinate_duplicates"] = int(gdf.duplicated(["lon", "lat"]).sum())
    (ROOT / "docs" / "export_log.json").write_text(
        json.dumps(log, ensure_ascii=False, indent=1)
    )
    print({k: v for k, v in log.items() if k != "files"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
