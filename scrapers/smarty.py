"""
Smarty.cz scraper – používá ScraperAPI proxy pro obejití blokování Railway IP.
"""
import json
import os
import requests
from bs4 import BeautifulSoup

BASE_SEARCH_URL = "https://www.smarty.cz/Vyhledavani?SearchText={query}"
BASE_URL = "https://www.smarty.cz"
SCRAPER_API_KEY = os.environ.get("SCRAPER_API_KEY", "")


def _proxied_url(url: str) -> str:
    return f"https://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}"


def _format_price(price_raw) -> str:
    try:
        return f"{int(price_raw):,} Kč".replace(",", " ")
    except Exception:
        return str(price_raw) + " Kč" if price_raw else "Neuvedena"


def _parse_gaitem(el) -> dict | None:
    try:
        raw = el.get("data-gaitem", "")
        if not raw:
            return None
        return json.loads(raw)
    except Exception:
        return None


def scrape_smarty(url: str) -> dict | None:
    try:
        resp = requests.get(_proxied_url(url), timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        name_el = soup.select_one("h1")
        name = name_el.get_text(strip=True) if name_el else "Neznámý produkt"

        gaitem_el = soup.select_one("[data-gaitem]")
        data = _parse_gaitem(gaitem_el) if gaitem_el else None
        price = _format_price(data.get("price")) if data else "Neuvedena"

        avail_el = (
            soup.select_one(".availability-text")
            or soup.select_one("[class*='avail']")
            or soup.select_one("[class*='stock']")
        )
        availability = avail_el.get_text(strip=True) if avail_el else "Neznámá"

        img_el = soup.select_one(".productList-item-img") or soup.select_one("img[alt]")
        image = img_el.get("src") if img_el else None
        if image and image.startswith("//"):
            image = "https:" + image

        return {"name": name, "price": price, "availability": availability, "image": image, "url": url}

    except Exception as e:
        print(f"[Smarty] Chyba při scrapování {url}: {e}")
        return None


def search_smarty(query: str) -> list[dict]:
    search_url = BASE_SEARCH_URL.format(query=query.replace(" ", "+"))
    results = []

    try:
        resp = requests.get(_proxied_url(search_url), timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        items = soup.select("[data-gaitem]")
        print(f"[Smarty] Nalezeno {len(items)} položek pro '{query}'")

        for item in items[:10]:
            try:
                data = _parse_gaitem(item)
                if not data:
                    continue
                if data.get("id") == "plachta.subcategory":
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

                print(f"[Smarty DEBUG] name={name}, price={price}, url={url}")

                if name and url:
                    results.append({
                        "name": name,
                        "price": price,
                        "availability": availability,
                        "url": url,
                    })
                    if len(results) >= 5:
                        break

            except Exception as e:
                print(f"[Smarty] Chyba při parsování položky: {e}")
                continue

    except Exception as e:
        print(f"[Smarty] Chyba při hledání '{query}': {e}")

    return results
