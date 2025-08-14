import re, requests, xml.etree.ElementTree as ET
from io import BytesIO

SOURCE = "https://feeds.audiomeans.fr/feed/b4a5ee3a-9230-4f9f-988d-2ae156a2d5a9.xml"
OUT    = "feed.xml"
MAX_ITEMS = 120  # réduis à 50 ou 30 si nécessaire
PATTERN = re.compile(r"\[(?:EXTRAIT|REDIFF|SNIPPET)\]", re.IGNORECASE)

def filter_rss(root):
    channel = root.find("channel")
    if channel is None:
        return False
    items = channel.findall("item")
    kept = []
    for it in items:
        t = it.findtext("title", default="")
        if not PATTERN.search(t or ""):
            kept.append(it)
        if len(kept) >= MAX_ITEMS:
            break
    for it in items: channel.remove(it)
    for it in kept: channel.append(it)
    return True

def filter_atom(root):
    ATOM = "{http://www.w3.org/2005/Atom}"
    entries = root.findall(ATOM + "entry")
    if not entries:
        return False
    kept = []
    for e in entries:
        title_el = e.find(ATOM + "title")
        t = "".join(title_el.itertext()) if title_el is not None else ""
        if not PATTERN.search(t or ""):
            kept.append(e)
        if len(kept) >= MAX_ITEMS:
            break
    for e in entries: root.remove(e)
    for e in kept: root.append(e)
    return True

def main():
    r = requests.get(SOURCE, timeout=30)
    r.raise_for_status()
    data = r.content

    tree = ET.parse(BytesIO(data))
    root = tree.getroot()

    if not (filter_rss(root) or filter_atom(root)):
        raise RuntimeError("Flux non reconnu (ni RSS2 ni Atom).")

    tree.write(OUT, encoding="utf-8", xml_declaration=True)
    print("OK ->", OUT)

if __name__ == "__main__":
    main()
