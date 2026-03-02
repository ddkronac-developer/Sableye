import discord
from discord.ext import commands, tasks
import asyncio
import os
from scrapers.smarty import scrape_smarty, search_smarty
from utils.watchlist import load_watchlist, save_watchlist

# ── Konfigurace ──────────────────────────────────────────────────────────────
TOKEN = os.environ["DISCORD_TOKEN"]
WATCH_INTERVAL_MINUTES = 30  # jak často kontrolovat ceny

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

watchlist = load_watchlist()


# ── Pomocné funkce ────────────────────────────────────────────────────────────
def product_embed(product: dict, url: str) -> discord.Embed:
    embed = discord.Embed(title=product["name"], url=url, color=discord.Color.orange())
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


@bot.command(name="hledat", help="Hledá produkty na Smarty. Použití: !hledat <dotaz>")
async def cmd_hledat(ctx, *, dotaz: str):
    async with ctx.typing():
        results = await asyncio.to_thread(search_smarty, dotaz)
    if not results:
        await ctx.send(f"🔍 Žádné výsledky pro **{dotaz}**.")
        return
    embed = discord.Embed(title=f"🔍 Výsledky pro '{dotaz}' – Smarty.cz", color=discord.Color.purple())
    for p in results[:5]:
        embed.add_field(
            name=p["name"][:100],
            value=f"💰 {p['price']} | 📦 {p['availability']}\n🔗 [Odkaz]({p['url']})",
            inline=False,
        )
    await ctx.send(embed=embed)


@bot.command(name="hlidat", help="Přidá produkt do hlídání ceny. Použití: !hlidat <url>")
async def cmd_hlidat(ctx, url: str):
    if "smarty.cz" not in url and "jrc.cz" not in url:
        await ctx.send("❌ Podporuji pouze smarty.cz a jrc.cz.")
        return
    async with ctx.typing():
        product = await asyncio.to_thread(scrape_smarty, url)
    if not product:
        await ctx.send("❌ Nepodařilo se načíst produkt. Zkontroluj URL.")
        return
    key = f"{ctx.author.id}:{url}"
    watchlist[key] = {
        "url": url,
        "last_price": product["price"],
        "channel_id": ctx.channel.id,
        "user_id": ctx.author.id,
        "username": str(ctx.author),
    }
    save_watchlist(watchlist)
    await ctx.send(f"✅ Hlídám **{product['name']}** za cenu **{product['price']}**. Upozorním tě při změně ceny.")


@bot.command(name="watchlist", help="Zobrazí tvůj aktuální watchlist.")
async def cmd_watchlist(ctx):
    user_items = [v for v in watchlist.values() if str(v["user_id"]) == str(ctx.author.id)]
    if not user_items:
        await ctx.send("📋 Tvůj watchlist je prázdný. Přidej produkt pomocí `!hlidat <url>`.")
        return
    embed = discord.Embed(title="📋 Tvůj watchlist", color=discord.Color.green())
    for item in user_items:
        embed.add_field(name=item["url"][:60] + "...", value=f"Poslední cena: {item['last_price']}", inline=False)
    await ctx.send(embed=embed)


@bot.command(name="odebrat", help="Odebere produkt z hlídání. Použití: !odebrat <url>")
async def cmd_odebrat(ctx, url: str):
    key = f"{ctx.author.id}:{url}"
    if key in watchlist:
        del watchlist[key]
        save_watchlist(watchlist)
        await ctx.send("✅ Produkt byl odebrán z watchlistu.")
    else:
        await ctx.send("❌ Tento produkt nemáš v watchlistu.")


# ── Automatické hlídání cen ───────────────────────────────────────────────────
@tasks.loop(minutes=WATCH_INTERVAL_MINUTES)
async def price_check_loop():
    for key, item in list(watchlist.items()):
        try:
            product = await asyncio.to_thread(scrape_smarty, item["url"])
            if not product:
                continue
            if product["price"] != item["last_price"]:
                channel = bot.get_channel(item["channel_id"])
                if channel:
                    embed = product_embed(product, item["url"])
                    embed.color = discord.Color.gold()
                    await channel.send(
                        f"🔔 <@{item['user_id']}> Změna ceny!\n"
                        f"Původní: **{item['last_price']}** → Nová: **{product['price']}**",
                        embed=embed,
                    )
                watchlist[key]["last_price"] = product["price"]
                save_watchlist(watchlist)
        except Exception as e:
            print(f"Chyba při kontrole {item['url']}: {e}")


# ── Start ─────────────────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"✅ Bot přihlášen jako {bot.user}")
    price_check_loop.start()


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Chybí argument. Zkus `!help {ctx.command}`.")
    else:
        print(f"Chyba: {error}")


bot.run(TOKEN)
