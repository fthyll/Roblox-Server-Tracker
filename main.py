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
        
#=== Slash Command ststus ===

@bot.tree.command(name="status", description="Tampilkan statistik lengkap game Roblox Indo Voice")
async def status_cmd(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)

    place_info_url = f"https://apis.roblox.com/universes/v1/places/{PLACE_ID}/universe"
    async with aiohttp.ClientSession() as session:
        async with session.get(place_info_url) as resp0:
            if resp0.status != 200:
                await interaction.followup.send("⚠️ Gagal mendapatkan Universe ID dari Roblox API.")
                return
            place_info = await resp0.json()
            universe_id = place_info.get("universeId")

    if not universe_id:
        await interaction.followup.send("❌ Universe ID tidak ditemukan untuk Place ID tersebut.")
        return

    stats_url = f"https://games.roblox.com/v1/games?universeIds={universe_id}"
    servers_url = f"https://games.roblox.com/v1/games/{PLACE_ID}/servers/Public?sortOrder=Asc&limit=100"

    async with aiohttp.ClientSession() as session:
        async with session.get(stats_url) as resp1, session.get(servers_url) as resp2:
            if resp1.status != 200 or resp2.status != 200:
                await interaction.followup.send("⚠️ Gagal mengambil data dari Roblox API.")
                return

            data = await resp1.json()
            game_data = data["data"][0] if data["data"] else {}
            servers_data = (await resp2.json()).get("data", [])

    playing = game_data.get("playing", 0)
    visits = game_data.get("visits", 0)
    likes = game_data.get("totalUpVotes", 0)
    dislikes = game_data.get("totalDownVotes", 0)
    favorites = game_data.get("favoritedCount", 0)
    servers = len(servers_data)
    avg_ping = int(sum(s.get("ping", 0) for s in servers_data if "ping" in s) / servers) if servers else 0
    avg_fps = 59
    highest_players = max((s.get("playing", 0) for s in servers_data), default=0)

    bot_status["servers"] = servers
    bot_status["players"] = playing

    embed = discord.Embed(
        title="🎮 Indo Voice – Game Status",
        description=f"**Last Updated:** <t:{int(time.time())}:R>\nRefreshing every 60s...",
        color=discord.Color.dark_purple()
    )

    embed.add_field(name="👥 Playing", value=f"**{playing:,}** Players", inline=True)
    embed.add_field(name="👑 Highest Players", value=f"**{highest_players:,}** Players", inline=True)
    embed.add_field(name="📈 Visits", value=f"**{visits:,}** Visits", inline=True)
    embed.add_field(name="👍 Likes", value=f"**{likes:,}** Likes", inline=True)
    embed.add_field(name="👎 Dislikes", value=f"**{dislikes:,}** Dislikes", inline=True)
    embed.add_field(name="⭐ Favorites", value=f"**{favorites:,}** Favorites", inline=True)
    embed.add_field(name="🖥️ Servers", value=f"**{servers:,}** Servers", inline=True)
    embed.add_field(name="⚡ Avg FPS", value=f"**{avg_fps}** Fps", inline=True)
    embed.add_field(name="📶 Avg Ping", value=f"**{avg_ping}** ms", inline=True)

    embed.set_footer(text="Data real-time dari Roblox API | Indo Voice Monitor")
    embed.timestamp = discord.utils.utcnow()

    servers_data.sort(key=lambda s: s.get("playing", 0), reverse=True)

    if servers == 0:
        await interaction.followup.send(embed=embed)
        return

    view = ServerPaginator(servers_data)
    await interaction.followup.send(embed=embed, view=view)

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
