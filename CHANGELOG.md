# 📋 Changelog

All notable changes to AI Friend Bot are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [4.0] - 2026-07-01 — Moderation System Edition

### 🆕 Added

- **11 new moderation commands**:
  - `/setarchitect @role` — Owner-only config: set the Architect role
  - `/setlog #channel` — Owner-only config: set the mod log channel
  - `/warn @user [reason]` — Issue a warning (persisted to JSON)
  - `/warnings [@user]` — List warnings for a user
  - `/clearwarnings @user [reason]` — Wipe all warnings
  - `/timeout @user <duration> [reason]` — Timeout with parsed duration (e.g., `1d`, `2h`)
  - `/untimeout @user [reason]` — Remove a timeout early
  - `/kick @user [reason]` — Kick a member
  - `/ban @user [days] [reason]` — Ban with optional message history deletion (0–7 days)
  - `/unban <user_id> [reason]` — Unban by user ID
  - `/purge <amount> [user]` — Bulk-delete messages (optionally filtered by user)
- **4-layer security model**:
  1. Auth check: Server owner OR Architect role
  2. Cannot moderate the server owner
  3. Cannot moderate the bot itself
  4. Role hierarchy: actor's top role > target's top role
  5. Bot role check: bot's top role > target's top role
- **Persistent storage**: `data/moderation.json` for warnings, role ID, and log channel ID
- **Mod log system**: All actions log to a configurable channel
- **DM notifications**: Users receive embeds about actions against them (graceful fallback)
- **Duration parser**: `Ns`, `Nm`, `Nh`, `Nd`, `Nw` formats (max 28 days)
- **Ephemeral responses** for mod commands (only the moderator sees confirmation)
- **Updated `/help`** with full moderation command list

### 🔄 Changed

- **Removed** `!clear` prefix command (replaced by `/purge` slash command)
- **Updated** error handler to catch `app_commands.BotMissingPermissions`
- **Enhanced** `/userinfo` and other embeds with more context

### 📚 Documentation

- **New**: `GUIDE.md` — comprehensive moderation system guide (737 lines)

---

## [3.0] - 2026-07-01 — Memory & Cooldowns Edition

### 🆕 Added

- **Per-user chat memory** for `/ask`:
  - Stores last 5 exchanges per user
  - 30-minute auto-expiry
  - In-memory storage (resets on bot restart)
  - `/memory` command to view stats (ephemeral)
  - `/forget` command to clear history (ephemeral)
- **Per-user cooldown** for `/ask`:
  - 10-second cooldown
  - Admin bypass for users with `Manage Server`
  - Ephemeral "slow down" message

### 🔄 Changed

- Updated footer to "AI Friend Bot v2.5"
- `/ask` now includes context indicator in embed footer

### ❌ Removed

- `!clear` prefix command and all its dependencies (later re-added in v4.0 as `/purge`)

---

## [2.6] - 2026-07-01 — Lean Edition

### 🆕 Added

- Standalone `/ask` with `OPENROUTER_API_KEY` support
- Cleaner help menu focused on core features

### ❌ Removed

- 10 utility/internet commands (`/search`, `/news`, `/weather`, `/joke`, `/quote`, `/time`, `/convert`, `/date`, `/calc`)
- All associated API clients, libraries, and helpers
- `.env.example` no longer references removed API keys

### 🎯 Goal

Focused bot with just AI chat, memory, info commands, and server utilities.

---

## [2.4] - 2026-07-01 — Internet & Utility Edition

### 🆕 Added

- 9 new commands:
  - `/search` — DuckDuckGo Instant Answer
  - `/news` — Google News RSS via rss2json
  - `/weather` — Open-Meteo (current + 3-day forecast)
  - `/joke` — JokeAPI (6 categories, safe mode)
  - `/quote` — ZenQuotes
  - `/time` — `zoneinfo` timezone lookup
  - `/convert` — Length, mass, temperature converter
  - `/date` — Day-of-year, season, weekend countdown
  - `/calc` — Safe math expression evaluator
- Optional `NEWS_API_KEY` and `TIMEZONE_API_KEY` in `.env.example`
- WMO weather code → emoji mapping
- 40+ city timezone aliases

---

## [2.3] - 2026-07-01 — Clean & Stable Edition

### 🆕 Added

- Reduced dependency list to 3 packages: `discord.py`, `requests`, `python-dotenv`
- `.env.example` template
- Improved error handling for OpenRouter

### ❌ Removed

- All document processing features (PDF, DOCX, TXT, CSV, MD)
- Image OCR (Tesseract)
- Pillow, pypdf, python-docx dependencies (caused Termux build failures)

### 🎯 Goal

A clean, Termux-friendly core bot that always works.

---

## [2.0] - 2026-07-01 — Slash Command Conversion

### 🔄 Changed

- **All commands converted to slash commands** (except `!clear`)
- `bot.tree.sync()` runs on `on_ready`
- New `app_commands` error handler

### 🆕 Added

- Embed-based responses with consistent styling
- `create_embed()` helper function
- `split_message()` helper for long responses

---

## [1.3] - 2026-07-01 — Security Update

### 🆕 Added

- `.env` file support via `python-dotenv`
- `.env.example` template
- `.gitignore` to exclude secrets

### 🔄 Changed

- **Removed hardcoded tokens** — now loaded from environment

### 🛡️ Security

- Bot token and API key no longer in source code

---

## [1.2] - Initial Stable Release

### 🆕 Added

- Discord bot with `discord.py`
- OpenRouter AI integration
- Basic slash commands:
  - `/ask`, `/hello`, `/ping`
  - `/userinfo`, `/avatar`, `/server`
  - `/help`, `/uptime`
- Prefix command `!clear` for moderation

### 📦 Dependencies

- `discord.py>=2.3.0`
- `requests>=2.31.0`
- `python-dotenv>=1.0.0`

---

## 🔮 Future Roadmap

### v5.0+ Ideas

- 📊 `/modstats` — Server moderation dashboard
- 🔇 `/mute` shortcut (alias for `/timeout`)
- 🔒 `/lockdown` — Lock a channel
- 📝 `/case <id>` — View specific mod action
- ⏰ Auto-moderation (anti-spam, raid detection)
- 💾 Backup/restore mod data
- 🌐 Multi-language support
- 🎮 Mini-games (8ball, dice, coin flip)
- 🔔 Reminders and timers
- 📈 Per-server analytics

---

## 📊 Version History Summary

| Version | Date | Theme | Commands |
|---|---|---|---|
| **4.0** | 2026-07-01 | Moderation System | 21 |
| 3.0 | 2026-07-01 | Memory & Cooldowns | 11 |
| 2.6 | 2026-07-01 | Lean Edition | 11 |
| 2.4 | 2026-07-01 | Internet & Utility | 19 |
| 2.3 | 2026-07-01 | Clean & Stable | 10 |
| 2.0 | 2026-07-01 | Slash Conversion | 10 |
| 1.3 | 2026-07-01 | Security Update | 8 |
| 1.2 | Initial | Initial Release | 8 |

---

*For detailed information on any version, see `GUIDE.md` and the source code in `bot.py`.*
