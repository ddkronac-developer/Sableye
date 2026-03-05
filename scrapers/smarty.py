"""
Smarty.cz scraper – využívá data-gaitem JSON atribut přímo v HTML,
což je spolehlivější než parsování CSS tříd.
"""
import json
import requests
from bs4 import BeautifulSoup

BASE_SEARCH_URL = "https://www.smarty.cz/Vyhledavani?SearchText={query}"
BASE_URL = "https://www.smarty.cz"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "cs-CZ,cs;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}


def _format_price(price_raw) -> str:
    """Převede číslo na čitelnou cenu v Kč."""
    try:
        return f"{int(price_raw):,} Kč".replace(",", " ")
    except Exception:
        return str(price_raw) + " Kč" if price_raw else "Neuvedena"


def _parse_gaitem(el) -> dict | None:
    """Vytáhne a naparsuje JSON z data-gaitem atributu."""
    try:
        raw = el.get("data-gaitem", "")
        if not raw:
            return None
        return json.loads(raw)
    except Exception:
        return None


def scrape_smarty(url: str) -> dict | None:
    """Scrapne detail produktu ze Smarty.cz. Vrátí slovník nebo None při chybě."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Název
        name_el = soup.select_one("h1")
        name = name_el.get_text(strip=True) if name_el else "Neznámý produkt"

        # Cena z data-gaitem
        gaitem_el = soup.select_one("[data-gaitem]")
        data = _parse_gaitem(gaitem_el) if gaitem_el else None
        price = _format_price(data.get("price")) if data else "Neuvedena"

        # Dostupnost
        avail_el = (
            soup.select_one(".availability-text")
            or soup.select_one("[class*='avail']")
            or soup.select_one("[class*='stock']")
        )
        availability = avail_el.get_text(strip=True) if avail_el else "Neznámá"

        # Obrázek
        img_el = soup.select_one(".productList-item-img") or soup.select_one(".gallery img") or soup.select_one("img[alt]")
        image = img_el.get("src") if img_el else None
        if image and image.startswith("//"):
            image = "https:" + image

        return {"name": name, "price": price, "availability": availability, "image": image, "url": url}

    except Exception as e:
        print(f"[Smarty] Chyba při scrapování {url}: {e}")
        return None


def search_smarty(query: str) -> list[dict]:
    """Vyhledá produkty na Smarty.cz pomocí data-gaitem JSON atributu."""
    search_url = BASE_SEARCH_URL.format(query=query.replace(" ", "+"))
    results = []

    try:
        resp = requests.get(search_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Produktové karty mají třídu productList-item a data-gaitem atribut s JSON daty
        items = soup.select(".productList-item[data-gaitem]")

        for item in items[:5]:
            try:
                data = _parse_gaitem(item)
                if not data:
                    continue

                name = data.get("name", "Neznámý produkt")
                price = _format_price(data.get("price") or data.get("fullPrice"))
                availability = data.get("available", "Neznámá")
                data_url = item.get("data-url", "")
                url = (BASE_URL + "/" + data_url.lstrip("/")) if data_url else None

                if not url:
                    link_el = item.select_one("a[href]")
                    href = link_el.get("href") if link_el else None
                    url = (BASE_URL + href) if href and href.startswith("/") else href

                if name and url:
                    results.append({
                        "name": name,
                        "price": price,
                        "availability": availability,
                        "url": url,
                    })
            except Exception as e:
                print(f"[Smarty] Chyba při parsování položky: {e}")
                continue

    except Exception as e:
        print(f"[Smarty] Chyba při hledání '{query}': {e}")

    return results
