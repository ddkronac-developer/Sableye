"""
Smarty.cz scraper (funguje i pro JRC – stejná skupina).
Smarty má méně agresivní ochranu než Alza, takže zkusíme nejdřív
jednoduchý requests+BeautifulSoup, Playwright jako záloha.
"""
import requests
from bs4 import BeautifulSoup

BASE_SEARCH_URL = "https://www.smarty.cz/Vyhledavani?SearchText={query}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "cs-CZ,cs;q=0.9",
}


def scrape_smarty(url: str) -> dict | None:
    """Scrapne detail produktu ze Smarty.cz. Vrátí slovník nebo None při chybě."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Název
        name_el = soup.select_one("h1") or soup.select_one(".product-name")
        name = name_el.get_text(strip=True) if name_el else "Neznámý produkt"

        # Cena – zkusíme více selektorů
        price_el = (
            soup.select_one(".price-final")
            or soup.select_one(".price")
            or soup.select_one("[class*='price']")
        )
        price = price_el.get_text(strip=True).replace("\xa0", " ") if price_el else "Neuvedena"

        # Dostupnost
        avail_el = soup.select_one(".availability") or soup.select_one("[class*='avail']") or soup.select_one("[class*='stock']")
        availability = avail_el.get_text(strip=True) if avail_el else "Neznámá"

        # Obrázek
        img_el = soup.select_one(".product-image img") or soup.select_one(".gallery img")
        image = img_el.get("src") if img_el else None
        if image and image.startswith("//"):
            image = "https:" + image

        return {"name": name, "price": price, "availability": availability, "image": image, "url": url}

    except Exception as e:
        print(f"[Smarty] Chyba při scrapování {url}: {e}")
        return None


def search_smarty(query: str) -> list[dict]:
    """Vyhledá produkty na Smarty.cz a vrátí seznam výsledků."""
    search_url = BASE_SEARCH_URL.format(query=query.replace(" ", "+"))
    results = []

    try:
        resp = requests.get(search_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Produktové karty – selektory uprav podle skutečné struktury stránky
        items = soup.select(".product-item") or soup.select(".item") or soup.select("[class*='product']")

        for item in items[:8]:
            try:
                name_el = item.select_one("h2, h3, .name, .title")
                price_el = item.select_one(".price-final, .price, [class*='price']")
                avail_el = item.select_one(".availability, [class*='avail']")
                link_el = item.select_one("a[href]")

                name = name_el.get_text(strip=True) if name_el else None
                price = price_el.get_text(strip=True).replace("\xa0", " ") if price_el else "Neuvedena"
                availability = avail_el.get_text(strip=True) if avail_el else "Neznámá"
                href = link_el.get("href") if link_el else None
                url = ("https://www.smarty.cz" + href) if href and href.startswith("/") else href

                if name and url:
                    results.append({"name": name, "price": price, "availability": availability, "url": url})
            except Exception:
                continue

    except Exception as e:
        print(f"[Smarty] Chyba při hledání '{query}': {e}")

    return results
