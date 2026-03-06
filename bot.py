import discord
from discord.ext import commands, tasks
import asyncio
import os
from scrapers.smarty import scrape_smarty
from utils.watchlist import load_watchlist, save_watchlist

# ── Konfigurace ──────────────────────────────────────────────────────────────
TOKEN = os.environ["DISCORD_TOKEN"]
WATCH_INTERVAL_MINUTES = 30
NOTIFY_CHANNEL_ID = int(os.environ.get("NOTIFY_CHANNEL_ID", "0"))

# Přednastavené produkty ke sledování
PRESET_PRODUCTS = [
    "https://www.smarty.cz/Pokemon-TCG-SV8-5-Prismatic-Evolutions-Booster-Bundle-4p212796",
    "https://www.smarty.cz/Pokemon-TCG-ME03-Perfect-Order-Elite-Trainer-Box-4p255654",
    "https://www.smarty.cz/Pokemon-TCG-SV10-5-Black-Bolt-Elite-Trainer-Box-4p231149",
    "https://www.smarty.cz/Pokemon-TCG-SV10-5-White-Flare-Elite-Trainer-Box-4p231148",
    "https://www.smarty.cz/Pokemon-TCG-SV10-5-Black-Bolt-Booster-Bundle-4p231155",
    "https://www.smarty.cz/Pokemon-TCG-SV10-5-White-Flare-Booster-Bundle-4p231154",
    https://www.smarty.cz/Pokemon-TCG-ME03-Perfect-Order-Booster-Box-36-boosteru--4p255656,
]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

watchlist = load_watchlist()


# ── Pomocné funkce ────────────────────────────────────────────────────────────
def product_embed(product: dict, url: str, changed: bool = False) -> discord.Embed:
    color = discord.Color.green() if changed else discord.Color.orange()
    embed = discord.Embed(title=product["name"], url=url, color=color)
    embed.add_field(name="💰 Cena", value=product["price"], inline=True)
    embed.add_field(name="📦 Dostupnost", value=product["availability"], inline=True)
    if product.get("image"):
        embed.set_thumbnail(url=product["image"])
    embed.set_footer(text="Smarty.cz / JRC")
    return embed


# ── Příkazy ───────────────────────────────────────────────────────────────────
@bot.command(name="produkt", help="Zobrazí info o produktu. Použití: !produkt <url>")
async def cmd_produkt(ctx, url: str):
    if "smarty.cz" not in url and "jrc.cz" not in url:
        await ctx.send("❌ Podporuji pouze smarty.cz a jrc.cz.")
        return
    async with ctx.typing():
        product = await asyncio.to_thread(scrape_smarty, url)
    if not product:
        await ctx.send("❌ Nepodařilo se načíst produkt. Zkontroluj URL.")
        return
    await ctx.send(embed=product_embed(product, url))


@bot.command(name="stav", help="Zobrazí aktuální stav všech sledovaných produktů.")
async def cmd_stav(ctx):
    await ctx.send("⏳ Načítám stav produktů, chvíli strpení...")
    for url in PRESET_PRODUCTS:
        async with ctx.typing():
            product = await asyncio.to_thread(scrape_smarty, url)
        if product:
            await ctx.send(embed=product_embed(product, url))
        else:
            await ctx.send(f"❌ Nepodařilo se načíst: {url}")
        await asyncio.sleep(2)


@bot.command(name="seznam", help="Vypíše seznam sledovaných produktů.")
async def cmd_seznam(ctx):
    embed = discord.Embed(title="📋 Sledované produkty", color=discord.Color.blue())
    for i, url in enumerate(PRESET_PRODUCTS, 1):
        name = url.split("/")[-1]
        embed.add_field(name=f"{i}.", value=f"[{name}]({url})", inline=False)
    await ctx.send(embed=embed)


# ── Automatické hlídání dostupnosti ──────────────────────────────────────────
@tasks.loop(minutes=WATCH_INTERVAL_MINUTES)
async def availability_check_loop():
    for url in PRESET_PRODUCTS:
        try:
            product = await asyncio.to_thread(scrape_smarty, url)
            if not product:
                continue

            key = f"preset:{url}"
            last = watchlist.get(key, {})
            last_avail = last.get("availability", "")
            last_price = last.get("price", "")

            changed = (last_avail and last_avail != product["availability"]) or \
                      (last_price and last_price != product["price"])

            if changed and NOTIFY_CHANNEL_ID:
                channel = bot.get_channel(NOTIFY_CHANNEL_ID)
                if channel:
                    embed = product_embed(product, url, changed=True)
                    msg = "🔔 **Změna dostupnosti nebo ceny!**\n"
                    if last_avail != product["availability"]:
                        msg += f"Dostupnost: **{last_avail}** → **{product['availability']}**\n"
                    if last_price != product["price"]:
                        msg += f"Cena: **{last_price}** → **{product['price']}**"
                    await channel.send(msg, embed=embed)

            watchlist[key] = {
                "url": url,
                "availability": product["availability"],
                "price": product["price"],
            }
            save_watchlist(watchlist)
            await asyncio.sleep(3)

        except Exception as e:
            print(f"Chyba při kontrole {url}: {e}")


# ── Start ─────────────────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"✅ Bot přihlášen jako {bot.user}")
    availability_check_loop.start()


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Chybí argument. Zkus `!help {ctx.command}`.")
    else:
        print(f"Chyba: {error}")


bot.run(TOKEN)
