"""Quote the content-use terms of a bureau's own page (a module, so that the tests can import it)."""

import re

# the three forms of the sentence found on the pages: the common one, the 関東/九州 one (ウェブサイト), the 東北 one
USE_START = re.compile(
    r"(当ホームページで公開している情報|[^ ]{2,12}ウェブサイトで掲載・発信している情報|当ホームページのコンテンツの利用については)"
)
USE_END = re.compile(r"(利用することができます。|に定めるとおりです。)")
IMPORTANT_START = re.compile(r"PDL1\.0に関する重要(情報|事項)")
IMPORTANT_END = re.compile(
    r"別の利用ルールの適用を明示しているコンテンツ|別の利用ルール"
)


def extract_terms(text: str) -> dict:
    m = USE_START.search(text)
    if not m:
        raise ValueError("no content-use sentence")
    e = USE_END.search(text, m.start())
    use = text[m.start() : e.end()].strip()
    imp = None
    k = text.find("出典の記載について", e.end())
    starts = [
        m for m in IMPORTANT_START.finditer(text, e.end(), k if k > 0 else len(text))
    ]
    i = starts[-1] if starts else None
    if i:
        j = IMPORTANT_END.search(text, k if k > 0 else i.start())
        imp = text[i.start() : (j.end() if j else i.start() + 1500)].strip()
        imp = re.sub(r"\s+", " ", imp)
    return {"use_sentence": re.sub(r"\s+", " ", use), "important": imp}
