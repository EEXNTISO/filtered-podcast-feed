import re, json, requests, xml.etree.ElementTree as ET
from io import BytesIO
from pathlib import Path

# Motifs à exclure dans le TITRE (insensible à la casse)
PATTERN = re.compile(r"\[(?:EXTRAIT|REDIFF?|SNIPPET)\]", re.IGNORECASE)

OUT_DIR = Path("public")
OUT_DIR.mkdir(exist_ok=True)

def filter_rss(root, max_items):
    channel = root.find("channel")
    if channel is None:
        return False
    items = channel.findall("item")
    kept = []
    for it in items:
        title = it.findtext("title", default="") or ""
        if not PATTERN.search(title):
            kept.append(it)
        if len(kept) >= max_items:
            break
    for it in items: channel.remove(it)
    for it in kept: channel.append(it)
    return True

def filter_atom(root, max_items):
    ATOM = "{http://www.w3.org/2005/Atom}"
    entries = root.findall(ATOM + "entry")
    if not entries:
        return False
    kept = []
    for e in entries:
        t_el = e.find(ATOM + "title")
        title = "".join(t_el.itertext()) if t_el is not None else ""
        if not PATTERN.search(title):
            kept.append(e)
        if len(kept) >= max_items:
            break
    for e in entries: root.remove(e)
    for e in kept: root.append(e)
    return True

def build_one(source_url: str, out_file: Path, max_items: int):
    r = requests.get(source_url, timeout=30)
    r.raise_for_status()
    tree = ET.parse(BytesIO(r.content))
    root = tree.getroot()
    if not (filter_rss(root, max_items) or filter_atom(root, max_items)):
        raise RuntimeError("Flux non reconnu (ni RSS2 ni Atom).")
    tree.write(out_file, encoding="utf-8", xml_declaration=True)
    print(f"OK -> {out_file}")

def main():
    # charge la config
    cfg = json.loads(Path("feeds.json").read_text(encoding="utf-8"))
    links = []
    for feed in cfg:
        slug = feed["slug"]
        source = feed["source"]
        max_items = int(feed.get("max_items", 50))
        out_file = OUT_DIR / f"{slug}.xml"
        build_one(source, out_file, max_items)
        links.append(f'<li><a href="./{slug}.xml">{slug}.xml</a></li>')
    # petite index pour éviter le 404 à la racine
    Path(OUT_DIR, "index.html").write_text(
        "<!doctype html><meta charset='utf-8'><h1>Filtered feeds</h1><ul>"
        + "".join(links) + "</ul>",
        encoding="utf-8"
    )

if __name__ == "__main__":
    main()
