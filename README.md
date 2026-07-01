# 🤖 AI Friend Bot v1.3

A powerful Discord bot powered by **OpenRouter AI** (free models), packed with utility, info, and moderation commands. Built with Python 3.13 and `discord.py`.

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![discord.py](https://img.shields.io/badge/discord.py-2.3%2B-5865F2?logo=discord)
![License](https://img.shields.io/badge/License-MIT-green)
![Termux](https://img.shields.io/badge/Termux-Supported-orange?logo=android)

---

## ✨ Features

- 🧠 **AI Chat** — Ask anything using `!ask`, powered by OpenRouter
- ℹ️ **User Info** — Detailed embeds with `!userinfo` and `!avatar`
- 🏠 **Server Stats** — View server details with `!server`
- 🛠️ **Moderation** — Bulk-delete messages with `!clear`
- ⏱️ **Uptime Tracking** — See how long the bot has been running
- 📖 **Help Menu** — Beautiful embed-based command list
- 🔒 **Secure** — Secrets stored in `.env` (never hardcoded)
- 📱 **Termux Ready** — Runs perfectly on Android via Termux

---

## 📋 Commands

| Command | Description | Permission |
|---|---|---|
| `!hello` | Greet the bot | Everyone |
| `!ask <question>` | Ask the AI anything | Everyone |
| `!ping` | Check bot latency | Everyone |
| `!help` | Show command menu | Everyone |
| `!userinfo [@user]` | Show user details | Everyone |
| `!avatar [@user]` | Show user avatar | Everyone |
| `!server` | Show server info | Everyone |
| `!uptime` | Bot session uptime | Everyone |
| `!clear <number>` | Bulk-delete messages (1–100) | Manage Messages |

---

## 🚀 Installation

### Prerequisites
- Python 3.10+ (tested on 3.13)
- A Discord bot token — [Create one here](https://discord.com/developers/applications)
- An OpenRouter API key — [Get one here](https://openrouter.ai/keys)

### 1️⃣ Clone or Download
```bash
git clone https://github.com/yourusername/ai-friend-bot.git
cd ai-friend-bot
```

### 2️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 3️⃣ Configure Secrets
Create a `.env` file in the project root:
```env
DISCORD_TOKEN=your_discord_bot_token_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

> ⚠️ **Never commit your `.env` file!** It's already in `.gitignore`.

### 4️⃣ Run the Bot
```bash
python bot.py
```

You should see:
```
✅ Logged in as YourBotName (ID: 123456789)
```

---

## 📱 Termux Setup (Android)

Run the bot on your phone 24/7!

### 1️⃣ Install Termux
Download from [F-Droid](https://f-droid.org/packages/com.termux/) (recommended) or Google Play.

### 2️⃣ Setup Environment
```bash
pkg update && pkg upgrade -y
pkg install python git -y
```

### 3️⃣ Clone & Install
```bash
cd ~
git clone https://github.com/yourusername/ai-friend-bot.git
cd ai-friend-bot
pip install -r requirements.txt
```

### 4️⃣ Create `.env`
Use `nano` to edit:
```bash
nano .env
```
Paste your keys:
```
DISCORD_TOKEN=your_token
OPENROUTER_API_KEY=your_key
```
Save: `CTRL + O` → Enter → `CTRL + X`

### 5️⃣ Run the Bot
```bash
python bot.py
```

### 🔄 Run in Background (24/7)
```bash
nohup python bot.py > bot.log 2>&1 &
```

**Useful commands:**
| Task | Command |
|---|---|
| View live logs | `tail -f bot.log` |
| Stop the bot | `pkill -f "python bot.py"` |
| Restart | `cd ~/ai-friend-bot && nohup python bot.py > bot.log 2>&1 &` |

---

## 🔐 Discord Bot Setup

### Required Intents (in Developer Portal)
Enable these under **Bot → Privileged Gateway Intents**:
- ✅ **Message Content Intent**
- ✅ **Server Members Intent**

### OAuth2 Invite URL
Replace `YOUR_CLIENT_ID` with your application's client ID:
```
https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=1099511627782&scope=bot
```

**Permissions included:**
- Send Messages
- Embed Links
- Read Message History
- Manage Messages (for `!clear`)
- Attach Files

---

## 📁 Project Structure

```
ai-friend-bot/
├── bot.py              # Main bot code
├── .env                # 🔐 Secrets (gitignored)
├── .gitignore          # Git exclusions
├── requirements.txt    # Python dependencies
├── README.md           # This file
└── CHANGELOG.md        # Version history
```

---

## 🛡️ Security

- ✅ Secrets are loaded from `.env` (never hardcoded)
- ✅ `.env` is excluded via `.gitignore`
- ✅ Bot validates secrets on startup — refuses to run if missing
- ✅ Permission checks on sensitive commands (`!clear`)

If you accidentally leak your token:
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. **Bot → Reset Token** immediately
3. Update your `.env` file

---

## 🐛 Troubleshooting

| Issue | Solution |
|---|---|
| `DISCORD_TOKEN not found` | Make sure `.env` is in the same folder as `bot.py` |
| `ModuleNotFoundError: dotenv` | Run `pip install python-dotenv` |
| `Missing Intents` warning | Enable Message Content + Server Members intents in Dev Portal |
| `!clear` says "Missing Permissions" | User needs `Manage Messages` permission in that channel |
| Bot offline after closing Termux | Use `nohup ... &` to run in background |
| `API Error` from `!ask` | Check your OpenRouter key and free model availability |

---

## 🗺️ Roadmap

- [ ] Slash command support (`/ask`, `/ping`, etc.)
- [ ] Conversation memory (per-user chat history)
- [ ] Rate limiting per user
- [ ] Music / media commands
- [ ] Database integration (SQLite/PostgreSQL)
- [ ] Docker support
- [ ] Web dashboard for stats

---

## 📜 License

This project is licensed under the **MIT License** — feel free to use, modify, and distribute.

---

## 🙏 Credits

- [discord.py](https://github.com/Rapptz/discord.py) — Discord API wrapper
- [OpenRouter](https://openrouter.ai/) — Unified AI model API
- Built with ❤️ for the Discord community

---

## 📞 Support

- 🐛 **Bug reports:** Open an issue on GitHub
- 💡 **Feature requests:** Open a discussion
- ⭐ **Like the project?** Give it a star!

---

**Made with 🐍 Python | Powered by 🤖 OpenRouter**
