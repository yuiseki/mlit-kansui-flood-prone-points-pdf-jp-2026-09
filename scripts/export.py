"""KML reading for kansui-flood-prone-points-jp (a module, so that the tests can import it)."""

import re
import xml.etree.ElementTree as ET
from urllib.parse import urljoin

K = "{http://www.opengis.net/kml/2.2}"
HREF = re.compile(r'href="([^"]+\.pdf)"', re.IGNORECASE)


def parse_kml(text: str, base: str) -> tuple[list[dict], int]:
    """Return the live Placemarks and the number of Placemarks that the publisher commented out (withdrawn)."""
    withdrawn = sum(
        1 for c in re.findall(r"<!--(.*?)-->", text, re.DOTALL) if "<Placemark>" in c
    )
    root = ET.fromstring(text.encode("utf-8"))
    rows = []
    for pm in root.iter(f"{K}Placemark"):
        name = pm.findtext(f"{K}name")
        coords = pm.findtext(f"{K}Point/{K}coordinates")
        parts = coords.strip().split(",")
        desc = pm.findtext(f"{K}description") or ""
        m = HREF.search(desc)
        href = m.group(1) if m else None
        url = urljoin(base + "/main/", href) if href else None
        if url and url.startswith("http://"):
            url = "https://" + url[len("http://") :]
        rows.append({
            "name": name.strip() if name else None,
            "lon": float(parts[0]), "lat": float(parts[1]),
            "pdf_href": href, "pdf_url": url,
            "pdf_key": url.rsplit("/", 1)[1][: -len(".pdf")] if url else None,
            "style_url": pm.findtext(f"{K}styleUrl"),
        })  # fmt: skip
    return rows, withdrawn
