"""
Jednoduchý persistentní watchlist uložený jako JSON soubor.
Na Railway se soubor resetuje při redeploymentu – pro produkci
doporučuji přejít na SQLite nebo Railway's PostgreSQL addon.
"""
import json
import os

WATCHLIST_FILE = "watchlist.json"


def load_watchlist() -> dict:
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_watchlist(watchlist: dict) -> None:
    with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(watchlist, f, ensure_ascii=False, indent=2)
