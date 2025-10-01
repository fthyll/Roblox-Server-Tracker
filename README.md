# 🤖 Discord Bot – Roblox Server Tracker

Bot ini dibuat untuk menampilkan **daftar server Roblox** dari sebuah `PLACE_ID` tertentu langsung di Discord.
Selain itu, bot ini dilengkapi dengan **Flask Web API** agar bisa dipantau secara online dan **Keep Alive** agar tetap berjalan 24/7 di Replit / VPS.

---

## ✨ Fitur

* ✅ **Slash Command `/servers`** → Menampilkan daftar server Roblox + jumlah pemain secara **real-time**.
* ✅ **Pagination** (navigasi server dengan tombol ⬅️ ➡️).
* ✅ **Flask Web API**

  * `/` → Menampilkan status bot.
  * `/status` → JSON berisi status bot, jumlah server, dan jumlah pemain.
* ✅ **Keep Alive System** untuk Replit agar bot tetap online 24/7.
* ✅ **Auto Restart** jika bot error / disconnect.

---

## 📦 Instalasi

### 1. Clone Repository

```bash
git clone https://github.com/username/roblox-discord-bot.git
cd roblox-discord-bot
```

### 2. Install Dependencies

Pastikan sudah ada **Python 3.10+** dan `pip`.

```bash
pip install -r requirements.txt
```

**requirements.txt** minimal:

```
discord.py
aiohttp
flask
requests
```

---

## ⚙️ Konfigurasi

Bot menggunakan **Environment Variables**. Buat file `.env` atau set langsung di Replit / VPS:

```
DISCORD_TOKEN=your_discord_bot_token
PLACE_ID=8356562067
REPL_URL=https://your-repl-url.repl.co
```

* `DISCORD_TOKEN` → Token bot Discord kamu.
* `PLACE_ID` → ID tempat/game Roblox yang ingin dipantau.
* `REPL_URL` → URL Replit agar bot bisa auto-keep alive.

---

## 🚀 Cara Menjalankan

Jalankan dengan:

```bash
python main.py
```

Jika di Replit, bot akan otomatis menjalankan Flask dan Keep Alive.

---

## 📡 Endpoint API

* `/` → Tes apakah bot online.
* `/status` → JSON status bot. Contoh respon:

```json
{
  "status": "online",
  "total_servers": 12,
  "total_players": 135
}
```

---

## 🕹️ Cara Pakai di Discord

1. Invite bot ke server kamu dengan link OAuth2 Discord Developer Portal.
2. Ketik command:

   ```
   /servers
   ```

   Bot akan menampilkan daftar server Roblox + tombol navigasi untuk berpindah halaman.

---

## 📷 Preview

![Preview Embed](https://i.imgur.com/VBCp1Uu.png)
*(Contoh tampilan daftar server Roblox di Discord)*

---

## 💡 Credits

👤 Dibuat oleh **@VeyH3H3H3H3**
⚡ Menggunakan **discord.py** + **aiohttp** + **Flask**

