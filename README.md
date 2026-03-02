# 🎮 Pokémon Bot – Smarty sledovač

Discord bot pro sledování Pokémon produktů na Smarty.cz a JRC.cz.

## Příkazy

| Příkaz | Popis | Příklad |
|--------|-------|---------|
| `!produkt <url>` | Zobrazí info o produktu | `!produkt https://www.smarty.cz/...` |
| `!hledat <dotaz>` | Hledá produkty na Smarty | `!hledat pokemon karty` |
| `!hlidat <url>` | Přidá produkt do sledování ceny | `!hlidat https://www.smarty.cz/...` |
| `!watchlist` | Zobrazí tvůj watchlist | `!watchlist` |
| `!odebrat <url>` | Odebere produkt z watchlistu | `!odebrat https://...` |

## Instalace lokálně

```bash
# 1. Nainstaluj závislosti
pip install -r requirements.txt
playwright install chromium

# 2. Nastav token
export DISCORD_TOKEN="tvůj_token_zde"

# 3. Spusť bota
python bot.py
```

## Nasazení na Railway

1. Vytvoř účet na [railway.app](https://railway.app)
2. Vytvoř nový projekt → **Deploy from GitHub repo**
3. Pushni tento kód na GitHub
4. V Railway nastav environment variable: `DISCORD_TOKEN = tvůj_token`
5. Railway automaticky použije `nixpacks.toml` a spustí bota

## Získání Discord tokenu

1. Jdi na [Discord Developer Portal](https://discord.com/developers/applications)
2. Vytvoř novou aplikaci → **Bot** → **Reset Token**
3. Povol intenty: `Message Content Intent` (v sekci Bot)
4. Pozvi bota na server: OAuth2 → URL Generator → `bot` → `Send Messages`, `Read Messages`

## Poznámky

- Bot funguje na **Smarty.cz i JRC.cz** (stejná skupina, stejný scraper)
- Scraper používá jednoduchý requests + BeautifulSoup – není potřeba žádný prohlížeč
- Selektory v `scrapers/smarty.py` může být potřeba **doladit** podle aktuální struktury stránek
- Watchlist se ukládá do `watchlist.json` – na Railway se resetuje při redeploymentu, pro produkci doporuč SQLite
