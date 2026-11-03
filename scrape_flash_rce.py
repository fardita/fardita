"""Scrape flash RCE Foto (Nikon) -> flash_rce.csv, poi filtra compatibili Z6 (i-TTL).
Uso: pip install playwright pandas && playwright install chromium && python scrape_flash_rce.py
NB: selettori CSS da verificare sulla pagina reale (non testati: host bloccato).
"""
import csv, re
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

BASE = "https://www.rcefoto.com/catalogo/digitale/nikon-compatible-d/flash-d/?pag={}"

def price(t):
    m = re.search(r"(\d{1,3}(?:\.\d{3})*,\d{2}|\d+(?:,\d{2})?)", t or "")
    return float(m.group(1).replace(".", "").replace(",", ".")) if m else None

rows = []
with sync_playwright() as p:
    page = p.chromium.launch().new_page()
    n = 1
    while True:
        page.goto(BASE.format(n), wait_until="networkidle")
        cards = page.query_selector_all(".product, .prodotto, .item-product, article")
        if not cards:
            break
        for c in cards:
            a = c.query_selector("a[href]")
            name = (c.query_selector("h2, h3, .title, .nome") or a)
            txt = c.inner_text()
            rows.append({
                "nome": name.inner_text().strip() if name else "",
                "prezzo": price((c.query_selector(".price, .prezzo") or c).inner_text()),
                "condizione": "usato" if re.search(r"usat", txt, re.I) else "nuovo",
                "url": urljoin(page.url, a.get_attribute("href")) if a else "",
            })
        n += 1

with open("flash_rce.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["nome", "prezzo", "condizione", "url"])
    w.writeheader(); w.writerows(rows)

# Z6: slitta Nikon standard, i-TTL. Esclude altri attacchi espliciti.
OTHER = re.compile(r"canon|sony|fuji|olympus|panasonic|pentax|\bm4/3\b|\bmft\b", re.I)
NIKON = re.compile(r"nikon|\bi-?ttl\b|\bsb-?\d|\bn\b|\(n\)", re.I)
z6 = sorted((r for r in rows if r["prezzo"] and NIKON.search(r["nome"]) and not OTHER.search(r["nome"])),
            key=lambda r: r["prezzo"])
for r in z6[:20]:
    print(f'{r["prezzo"]:>8.2f}  {r["condizione"]:<6}  {r["nome"]}  {r["url"]}')
