import os
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import asyncio
import threading
from flask import Flask, jsonify
import requests
import time

# === KONFIGURASI ===
TOKEN = os.getenv("DISCORD_TOKEN")
PLACE_ID = int(os.getenv("PLACE_ID", 8356562067))
if not TOKEN:
    raise ValueError("❌ ERROR: DISCORD_TOKEN belum di-set di ENV!")

# Variabel global untuk menyimpan status
bot_status = {"online": False, "servers": 0, "players": 0}

# === Flask Web Keep Alive + Status API ===
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot Roblox sedang berjalan di Replit 24/7!"

@app.route('/status')
def status():
    return jsonify({
        "status": "online" if bot_status["online"] else "offline",
        "total_servers": bot_status["servers"],
        "total_players": bot_status["players"]
    })

def run_flask():
    app.run(host="0.0.0.0", port=5000)

def keep_alive():
    url = os.getenv("REPL_URL")
    if not url:
        print("⚠️ REPL_URL belum di-set, auto-ping tidak aktif.")
        return
    while True:
        try:
            requests.get(url)
            print("🔄 Keep-alive ping ke:", url)
        except Exception as e:
            print("❌ Gagal ping:", e)
        time.sleep(300)

threading.Thread(target=run_flask, daemon=True).start()
threading.Thread(target=keep_alive, daemon=True).start()

# === Discord Bot ===
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

async def fetch_servers():
    url = f"https://games.roblox.com/v1/games/{PLACE_ID}/servers/Public?sortOrder=Asc&limit=100"
    servers = []
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                for s in data.get("data", []):
                    servers.append({
                        "id": s["id"],
                        "playing": s.get("playing", 0),
                        "maxPlayers": s.get("maxPlayers", 0),
                        "ping": s.get("ping", "N/A")
                    })
    # Update global status setiap kali fetch
    bot_status["servers"] = len(servers)
    bot_status["players"] = sum(s['playing'] for s in servers)
    return servers

class ServerPaginator(discord.ui.View):
    def __init__(self, data, per_page=10):
        super().__init__(timeout=None)
        self.data = data
        self.per_page = min(per_page, 25)
        self.current_page = 0
        self.max_page = (len(data) - 1) // self.per_page

    def get_embed(self):
        total_players = sum(s['playing'] for s in self.data)
        embed = discord.Embed(
            title=f"🌐 Indo Voice Server List",
            description=f"📊 **Total Server:** {len(self.data)} | 👥 **Total Pemain:** {total_players}",
            color=discord.Color.blurple()
        )
        start = self.current_page * self.per_page
        end = start + self.per_page
        for s in self.data[start:end]:
            join_url = f"https://www.roblox.com/games/start?placeId={PLACE_ID}&serverId={s['id']}"
            short_id = s['id'][-4:].upper()
            embed.add_field(
                name=f"🖥️ Server `{short_id}` | 👥 {s['playing']}/{s['maxPlayers']}",
                value=f"📍 **Ping:** {s['ping']} ms\n🔗 [🎮 JOIN SERVER]({join_url})",
                inline=False
            )
        embed.set_footer(text="Bot by @VeyH3H3H3H3 | Gunakan ⬅️ ➡️ untuk pindah halaman")
        return embed

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < self.max_page:
            self.current_page += 1
            await interaction.response.edit_message(embed=self.get_embed(), view=self)

@bot.event
async def on_ready():
    bot_status["online"] = True
    print(f"✅ Bot sudah online sebagai {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Slash commands global disinkronkan: {len(synced)}")
    except Exception as e:
        print(f"❌ Gagal sync command: {e}")

@bot.tree.command(name="servers", description="Tampilkan daftar server Roblox + jumlah pemain real-time")
async def servers_cmd(interaction: discord.Interaction):
    await interaction.response.defer()
    servers = await fetch_servers()
    if not servers:
        await interaction.followup.send("❌ Tidak ada server yang aktif.")
        return
    paginator = ServerPaginator(servers)
    await interaction.followup.send(embed=paginator.get_embed(), view=paginator)

async def main():
    async with bot:
        while True:
            try:
                await bot.start(TOKEN)
            except Exception as e:
                bot_status["online"] = False
                print(f"⚠️ Bot error: {e}, restart dalam 5 detik...")
                await asyncio.sleep(5)

try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    asyncio.run(main())
else:
    loop.create_task(main())
    print("⚠️ Bot dijalankan di event loop yang sudah ada (misal Jupyter/Colab).")
