"""
Smarty.cz scraper – používá ScraperAPI proxy + render=true pro JS obsah.
"""
import json
import os
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.smarty.cz"
SCRAPER_API_KEY = os.environ.get("SCRAPER_API_KEY", "")


def _proxied_url(url: str) -> str:
    return f"https://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}&render=true"


def _format_price(price_raw) -> str:
    try:
        return f"{int(price_raw):,} Kč".replace(",", " ")
    except Exception:
        return str(price_raw) + " Kč" if price_raw else "Neuvedena"


def scrape_smarty(url: str) -> dict | None:
    try:
        resp = requests.get(_proxied_url(url), timeout=60)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Název
        name_el = soup.select_one("h1")
        name = name_el.get_text(strip=True) if name_el else "Neznámý produkt"

        # Cena – zkusíme více selektorů
        price = "Neuvedena"
        for selector in [".price-final", ".price-value", "[class*='price']", ".price"]:
            el = soup.select_one(selector)
            if el:
                text = el.get_text(strip=True).replace("\xa0", " ").replace(" ", " ")
                if any(c.isdigit() for c in text):
                    price = text
                    break

        # Dostupnost
        availability = "Neznámá"
        for selector in [".availability", "[class*='avail']", "[class*='stock']", ".delivery"]:
            el = soup.select_one(selector)
            if el:
                text = el.get_text(strip=True)
                if text:
                    availability = text
                    break

        # Obrázek
        img_el = soup.select_one("img.productList-item-img") or soup.select_one(".product-image img")
        image = img_el.get("src") if img_el else None
        if image and image.startswith("//"):
            image = "https:" + image

        print(f"[Smarty] Scrapováno: {name} | {price} | {availability}")
        return {"name": name, "price": price, "availability": availability, "image": image, "url": url}

    except Exception as e:
        print(f"[Smarty] Chyba při scrapování {url}: {e}")
        return None


def search_smarty(query: str) -> list[dict]:
    """Vyhledávání není podporováno – použij !hlidat s přímou URL produktu."""
    return []
