# ==========================================================
# AI Friend Bot v4.0 — Moderation System Edition
# Author: [Your Name]
# Description:
#   Discord bot with AI chat (with memory) and a full
#   moderation system. Includes user/server info, uptime,
#   ping, and Architect-only mod commands.
#
# Compatible with: Python 3.13, discord.py 2.3+
# Secrets loaded from .env (see .env.example).
# ==========================================================

import os
import re
import json
import time
import discord
import requests
import datetime
from pathlib import Path
from collections import deque
from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands

# ==========================
# LOAD ENVIRONMENT VARIABLES
# ==========================

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

try:
    TOKEN = os.getenv("DISCORD_TOKEN")
    API_KEY = os.getenv("OPENROUTER_API_KEY")
except Exception as e:
    raise RuntimeError(f"❌ Failed to load environment variables: {e}")

if not TOKEN:
    raise RuntimeError(
        "❌ DISCORD_TOKEN not found in .env file.\n"
        "   Create a .env file with: DISCORD_TOKEN=your_token_here"
    )
if not API_KEY:
    raise RuntimeError(
        "❌ OPENROUTER_API_KEY not found in .env file.\n"
        "   Create a .env file with: OPENROUTER_API_KEY=your_key_here"
    )

# ==========================
# CONFIGURATION
# ==========================

MODEL = "openai/gpt-oss-120b:free"

START_TIME = datetime.datetime.now(datetime.timezone.utc)
EMBED_COLOR = discord.Color.blue()

# Cooldown for /ask
ASK_COOLDOWN = 10
cooldowns = {}

# ==========================
# CHAT MEMORY CONFIGURATION
# ==========================

MAX_MEMORY_EXCHANGES = 5
MEMORY_TIMEOUT = 30 * 60  # 30 minutes
chat_memory = {}

# ==========================
# MODERATION DATA (v4.0 NEW)
# ==========================

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)  # Create data/ if missing
MOD_DATA_FILE = DATA_DIR / "moderation.json"

# Structure:
# {
#   "<guild_id>": {
#       "architect_role_id": <int or null>,
#       "log_channel_id": <int or null>,
#       "warnings": {
#           "<user_id>": [
#               {"reason": str, "moderator_id": int, "timestamp": str}
#           ]
#       }
#   }
# }


def load_mod_data() -> dict:
    """Load moderation data from JSON file."""
    if not MOD_DATA_FILE.exists():
        return {}
    try:
        with open(MOD_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"⚠️ Failed to load mod data: {e}. Starting fresh.")
        return {}


def save_mod_data(data: dict):
    """Save moderation data to JSON file."""
    try:
        with open(MOD_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except OSError as e:
        print(f"❌ Failed to save mod data: {e}")


# Load on startup
mod_data = load_mod_data()


def get_guild_data(guild_id: int) -> dict:
    """Get or create a guild's moderation data entry."""
    gid = str(guild_id)
    if gid not in mod_data:
        mod_data[gid] = {
            "architect_role_id": None,
            "log_channel_id": None,
            "warnings": {}
        }
    # Ensure all keys exist (forward-compat)
    mod_data[gid].setdefault("architect_role_id", None)
    mod_data[gid].setdefault("log_channel_id", None)
    mod_data[gid].setdefault("warnings", {})
    return mod_data[gid]


# ==========================
# DISCORD SETUP
# ==========================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.moderation = True  # For timeout events (optional)

bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command("help")


# ==========================
# HELPER FUNCTIONS
# ==========================

def create_embed(title: str, description: str = "", color=None) -> discord.Embed:
    """Create a standardized embed with consistent styling."""
    embed = discord.Embed(
        title=title,
        description=description if description else discord.Embed.Empty,
        color=color if color else EMBED_COLOR,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
    embed.set_footer(text="AI Friend Bot v4.0")
    return embed


def split_message(text: str, limit: int = 1900) -> list:
    """Split long text into Discord-friendly chunks."""
    return [text[i:i + limit] for i in range(0, len(text), limit)]


# ==========================
# COOLDOWN HELPER
# ==========================

def check_ask_cooldown(user_id: int) -> tuple[bool, float]:
    """Check if a user is on cooldown for /ask."""
    now = time.time()
    if user_id in cooldowns:
        elapsed = now - cooldowns[user_id]
        if elapsed < ASK_COOLDOWN:
            return False, ASK_COOLDOWN - elapsed
    cooldowns[user_id] = now
    return True, 0


# ==========================
# CHAT MEMORY HELPERS
# ==========================

def get_user_memory(user_id: int) -> dict:
    """Get or create a user's chat memory."""
    now = time.time()
    if user_id not in chat_memory:
        chat_memory[user_id] = {
            "messages": deque(maxlen=MAX_MEMORY_EXCHANGES * 2),
            "last_active": now
        }
    elif now - chat_memory[user_id]["last_active"] > MEMORY_TIMEOUT:
        chat_memory[user_id]["messages"].clear()
    chat_memory[user_id]["last_active"] = now
    return chat_memory[user_id]


def add_to_memory(user_id: int, user_message: str, assistant_message: str):
    """Add an exchange to memory."""
    memory = get_user_memory(user_id)
    memory["messages"].append({"role": "user", "content": user_message})
    memory["messages"].append({"role": "assistant", "content": assistant_message})


def clear_user_memory(user_id: int) -> bool:
    """Clear a user's chat memory."""
    if user_id in chat_memory and chat_memory[user_id]["messages"]:
        chat_memory[user_id]["messages"].clear()
        return True
    return False


def get_memory_stats(user_id: int) -> dict:
    """Get memory statistics."""
    if user_id not in chat_memory:
        return {"exchanges": 0, "age_seconds": None}
    memory = chat_memory[user_id]
    exchanges = len(memory["messages"]) // 2
    age = time.time() - memory["last_active"] if memory["last_active"] else None
    return {"exchanges": exchanges, "age_seconds": age}


# ==========================
# MODERATION HELPERS (v4.0 NEW)
# ==========================

def is_owner(member: discord.Member) -> bool:
    """Check if member is the server owner."""
    return member.id == member.guild.owner_id


def is_architect(member: discord.Member) -> bool:
    """Check if member has the configured Architect role."""
    if is_owner(member):
        return True
    guild_data = get_guild_data(member.guild.id)
    role_id = guild_data.get("architect_role_id")
    if not role_id:
        return False
    return any(r.id == role_id for r in member.roles)


def has_mod_access(member: discord.Member) -> bool:
    """Check if member can use moderation commands (Owner or Architect)."""
    return is_owner(member) or is_architect(member)


def can_moderate(actor: discord.Member, target: discord.Member) -> tuple[bool, str]:
    """
    Check if `actor` can moderate `target` based on role hierarchy.
    Returns (allowed, reason_if_not).
    """
    # Server owner cannot be moderated
    if target.id == target.guild.owner_id:
        return False, "🚫 Cannot moderate the **server owner**."

    # The bot itself cannot be moderated by this bot
    if target.id == bot.user.id:
        return False, "🚫 Cannot moderate **myself**."

    # Actor must outrank target
    if actor.top_role.position <= target.top_role.position and actor.id != target.guild.owner_id:
        return False, (
            f"🚫 You cannot moderate {target.mention} — they have an **equal or higher role** than you."
        )

    # Bot must outrank target (to perform the action)
    if bot.user.id != target.guild.owner_id:
        bot_top = target.guild.me.top_role
        if bot_top.position <= target.top_role.position:
            return False, (
                f"❌ I cannot moderate {target.mention} — their role is **higher than mine**.\n"
                f"💡 Move my role above theirs in Server Settings → Roles."
            )

    return True, ""


def parse_duration(duration_str: str) -> datetime.timedelta | None:
    """
    Parse a duration string like '1d', '12h', '30m', '90s' into a timedelta.
    Returns None if invalid.
    """
    pattern = re.compile(r"^(\d+)\s*([smhdw])$", re.IGNORECASE)
    match = pattern.match(duration_str.strip())
    if not match:
        return None

    value, unit = match.groups()
    value = int(value)
    if value <= 0:
        return None

    units = {
        "s": 1,
        "m": 60,
        "h": 3600,
        "d": 86400,
        "w": 604800,
    }
    return datetime.timedelta(seconds=value * units[unit.lower()])


def format_timedelta(td: datetime.timedelta) -> str:
    """Format a timedelta as 'Xd Yh Zm'."""
    total = int(td.total_seconds())
    days, remainder = divmod(total, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds and not days:
        parts.append(f"{seconds}s")
    return " ".join(parts) if parts else "0m"


async def send_mod_log(guild: discord.Guild, embed: discord.Embed):
    """Send a moderation log embed to the configured log channel."""
    guild_data = get_guild_data(guild.id)
    log_channel_id = guild_data.get("log_channel_id")
    if not log_channel_id:
        return  # No log channel configured

    channel = guild.get_channel(log_channel_id)
    if not channel:
        return

    try:
        await channel.send(embed=embed)
    except discord.Forbidden:
        pass
    except discord.HTTPException as e:
        print(f"⚠️ Failed to send mod log: {e}")


async def try_dm_user(user: discord.abc.User, embed: discord.Embed) -> bool:
    """Try to DM a user. Returns True if successful."""
    try:
        await user.send(embed=embed)
        return True
    except (discord.Forbidden, discord.HTTPException):
        return False


# ==========================
# OPENROUTER API CALLER
# ==========================

async def call_openrouter(prompt: str, system: str = None, history: list = None, max_retries: int = 2) -> str:
    """Call OpenRouter API with a prompt and optional system message + conversation history."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": prompt})

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://localhost",
        "X-Title": "AI Friend Bot v4.0"
    }

    data = {"model": MODEL, "messages": messages}

    for attempt in range(max_retries + 1):
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=120
            )
            result = response.json()

            if response.status_code == 200:
                return result["choices"][0]["message"]["content"]

            if attempt < max_retries:
                continue
            return f"❌ API Error (status {response.status_code}): {result}"

        except requests.exceptions.Timeout:
            if attempt < max_retries:
                continue
            return "❌ Request timed out. The AI service is slow right now."
        except Exception as e:
            return f"❌ Error: {e}"

    return "❌ Failed after multiple attempts."


# ==========================
# EVENTS
# ==========================

@bot.event
async def on_ready():
    """Triggered when the bot successfully connects to Discord."""
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"❌ Slash command sync failed: {e}")

    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")


# ==========================================================
# AI COMMANDS
# ==========================================================

@bot.tree.command(name="hello", description="Send a friendly greeting")
async def slash_hello(interaction: discord.Interaction):
    await interaction.response.send_message("👋 Hello! I am online and ready to help.")


@bot.tree.command(name="ping", description="Check the bot's latency")
async def slash_ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    embed = create_embed(title="🏓 Pong!", description=f"Latency: **{latency} ms**")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="ask", description="Ask the AI a question (with chat memory)")
@app_commands.describe(question="The question you want to ask the AI")
async def slash_ask(interaction: discord.Interaction, question: str):
    is_admin = interaction.user.guild_permissions.manage_guild if interaction.guild else False
    if not is_admin:
        allowed, remaining = check_ask_cooldown(interaction.user.id)
        if not allowed:
            await interaction.response.send_message(
                f"⏳ Slow down! Try again in **{remaining:.1f}s**.\n"
                f"💡 Use `/forget` to clear chat memory.",
                ephemeral=True
            )
            return

    await interaction.response.defer(thinking=True)

    memory = get_user_memory(interaction.user.id)
    history = list(memory["messages"]) if memory["messages"] else None

    async with interaction.channel.typing():
        answer = await call_openrouter(prompt=question, history=history)

    add_to_memory(interaction.user.id, question, answer)

    embed = create_embed(title="💬 AI Response", description=answer)
    if history:
        embed.set_footer(text=f"AI Friend Bot v4.0 • Context: {len(history) // 2} previous exchange(s)")
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="memory", description="Show your chat memory stats")
async def slash_memory(interaction: discord.Interaction):
    stats = get_memory_stats(interaction.user.id)

    embed = create_embed(
        title="🧠 Your Chat Memory",
        description=(
            f"**Stored exchanges:** {stats['exchanges']} / {MAX_MEMORY_EXCHANGES}\n"
            f"**Auto-expire:** {MEMORY_TIMEOUT // 60} minutes idle"
        )
    )

    if stats["age_seconds"] is not None:
        if stats["age_seconds"] < 60:
            age_str = f"{stats['age_seconds']:.0f}s ago"
        elif stats["age_seconds"] < 3600:
            age_str = f"{stats['age_seconds'] / 60:.1f} min ago"
        else:
            age_str = f"{stats['age_seconds'] / 3600:.1f} hours ago"
        embed.add_field(name="⏱️ Last Active", value=age_str, inline=True)

    if stats["exchanges"] == 0:
        embed.add_field(
            name="💡 Tip",
            value="Memory is empty. Use `/ask` to start a conversation!",
            inline=False
        )
    else:
        embed.add_field(
            name="💡 Tip",
            value="Use `/forget` to clear your memory and start fresh.",
            inline=False
        )

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="forget", description="Clear your chat memory with the AI")
async def slash_forget(interaction: discord.Interaction):
    cleared = clear_user_memory(interaction.user.id)
    if cleared:
        embed = create_embed(
            title="🧹 Memory Cleared",
            description="Your conversation history has been wiped. The AI will start fresh!",
            color=discord.Color.green()
        )
    else:
        embed = create_embed(
            title="🧹 Nothing to Clear",
            description="You don't have any active memory. The bot was already starting fresh!",
            color=discord.Color.greyple()
        )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ==========================================================
# INFO COMMANDS
# ==========================================================

@bot.tree.command(name="help", description="Show all available bot commands")
async def slash_help(interaction: discord.Interaction):
    embed = create_embed(
        title="📖 AI Friend Bot v4.0 — Help Menu",
        description="Here are all the commands you can use:"
    )
    embed.add_field(
        name="🤖 AI Commands",
        value=(
            "`/ask <question>` — Ask the AI (with chat memory!)\n"
            "`/memory` — View your conversation stats\n"
            "`/forget` — Clear your chat history\n"
            "`/hello` — Greet the bot"
        ),
        inline=False
    )
    embed.add_field(
        name="ℹ️ Info Commands",
        value=(
            "`/userinfo [@user]` — Show user information\n"
            "`/avatar [@user]` — Show user avatar\n"
            "`/server` — Show server information\n"
            "`/uptime` — Show how long the bot has been running\n"
            "`/ping` — Check bot latency\n"
            "`/help` — Show this help menu"
        ),
        inline=False
    )
    embed.add_field(
        name="🛡️ Moderation (Owner & Architect Only)",
        value=(
            "`/warn @user [reason]` — Issue a warning\n"
            "`/warnings [@user]` — List warnings\n"
            "`/clearwarnings @user` — Clear all warnings\n"
            "`/timeout @user <duration> [reason]` — Timeout (e.g., `1d`)\n"
            "`/untimeout @user [reason]` — Remove timeout\n"
            "`/kick @user [reason]` — Kick member\n"
            "`/ban @user [days] [reason]` — Ban member\n"
            "`/unban <user_id> [reason]` — Unban by ID\n"
            "`/purge <amount> [user]` — Bulk delete messages"
        ),
        inline=False
    )
    embed.add_field(
        name="⚙️ Mod Setup (Owner Only)",
        value=(
            "`/setarchitect @role` — Set the Architect role\n"
            "`/setlog #channel` — Set the mod log channel"
        ),
        inline=False
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="userinfo", description="Show information about a user")
@app_commands.describe(member="The user to show info about (defaults to you)")
async def slash_userinfo(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    account_created = member.created_at.strftime("%b %d, %Y")
    joined_at = member.joined_at.strftime("%b %d, %Y") if member.joined_at else "N/A"

    embed = create_embed(
        title=f"👤 User Info: {member.display_name}",
        description=f"Information about {member.mention}"
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="🆔 User ID", value=member.id, inline=True)
    embed.add_field(name="📛 Display Name", value=member.display_name, inline=True)
    embed.add_field(name="🟢 Status", value=str(member.status).capitalize(), inline=True)
    embed.add_field(name="📅 Account Created", value=account_created, inline=True)
    embed.add_field(name="📥 Joined Server", value=joined_at, inline=True)
    embed.add_field(name="🤖 Bot?", value="Yes" if member.bot else "No", inline=True)
    top_role = member.top_role.mention if member.top_role.name != "@everyone" else "None"
    embed.add_field(name="🎭 Top Role", value=top_role, inline=True)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="avatar", description="Show a user's avatar")
@app_commands.describe(member="The user whose avatar to show (defaults to you)")
async def slash_avatar(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    embed = create_embed(
        title=f"🖼️ Avatar: {member.display_name}",
        description=f"[Click here for full image]({member.display_avatar.url})"
    )
    embed.set_image(url=member.display_avatar.url)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="server", description="Show information about the current server")
async def slash_server(interaction: discord.Interaction):
    guild = interaction.guild
    humans = sum(1 for m in guild.members if not m.bot)
    bots = sum(1 for m in guild.members if m.bot)

    embed = create_embed(
        title=f"🏠 Server: {guild.name}",
        description=guild.description if guild.description else "No description set."
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(name="🆔 Server ID", value=guild.id, inline=True)
    embed.add_field(name="👑 Owner", value=guild.owner.mention if guild.owner else "N/A", inline=True)
    embed.add_field(name="📅 Created On", value=guild.created_at.strftime("%b %d, %Y"), inline=True)
    embed.add_field(name="👥 Members", value=f"{guild.member_count} total ({humans} humans, {bots} bots)", inline=True)
    embed.add_field(name="💬 Channels", value=len(guild.channels), inline=True)
    embed.add_field(name="🎭 Roles", value=len(guild.roles), inline=True)
    embed.add_field(name="🔒 Verification", value=str(guild.verification_level).capitalize(), inline=True)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="uptime", description="Show how long the bot has been running")
async def slash_uptime(interaction: discord.Interaction):
    delta = datetime.datetime.now(datetime.timezone.utc) - START_TIME
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    embed = create_embed(
        title="⏱️ Bot Uptime",
        description=f"I've been online for:\n**{days}d {hours}h {minutes}m {seconds}s**"
    )
    await interaction.response.send_message(embed=embed)


# ==========================================================
# MODERATION SETUP (v4.0 NEW) — OWNER ONLY
# ==========================================================

@bot.tree.command(name="setarchitect", description="[OWNER] Set the Architect role that can use mod commands")
@app_commands.describe(role="The role to grant moderation access to")
async def slash_setarchitect(interaction: discord.Interaction, role: discord.Role):
    if interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message(
            "🚫 Only the **server owner** can configure the Architect role.",
            ephemeral=True
        )
        return

    guild_data = get_guild_data(interaction.guild.id)
    guild_data["architect_role_id"] = role.id
    save_mod_data(mod_data)

    embed = create_embed(
        title="⚙️ Architect Role Set",
        description=f"The {role.mention} role can now use moderation commands.\n\n"
                    f"💡 Server owners always have access, regardless of roles.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

    # Log it
    log_embed = create_embed(
        title="⚙️ Architect Role Configured",
        description=f"**Role:** {role.mention} (`{role.id}`)\n**Set by:** {interaction.user.mention}",
        color=discord.Color.blue()
    )
    await send_mod_log(interaction.guild, log_embed)


@bot.tree.command(name="setlog", description="[OWNER] Set the channel for moderation logs")
@app_commands.describe(channel="The channel where mod actions are logged")
async def slash_setlog(interaction: discord.Interaction, channel: discord.TextChannel):
    if interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message(
            "🚫 Only the **server owner** can configure the log channel.",
            ephemeral=True
        )
        return

    # Check bot can send in the channel
    if not channel.permissions_for(interaction.guild.me).send_messages:
        await interaction.response.send_message(
            f"❌ I don't have permission to send messages in {channel.mention}.",
            ephemeral=True
        )
        return

    guild_data = get_guild_data(interaction.guild.id)
    guild_data["log_channel_id"] = channel.id
    save_mod_data(mod_data)

    embed = create_embed(
        title="📝 Log Channel Set",
        description=f"Moderation actions will be logged to {channel.mention}.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

    # Send a test log
    log_embed = create_embed(
        title="📝 Mod Log Channel Configured",
        description=f"**Channel:** {channel.mention}\n**Set by:** {interaction.user.mention}",
        color=discord.Color.blue()
    )
    await send_mod_log(interaction.guild, log_embed)


# ==========================================================
# MODERATION COMMANDS (v4.0 NEW) — OWNER + ARCHITECT
# ==========================================================

# ---- /warn ----
@bot.tree.command(name="warn", description="Issue a warning to a user")
@app_commands.describe(user="The user to warn", reason="Reason for the warning")
async def slash_warn(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    if not has_mod_access(interaction.user):
        await interaction.response.send_message(
            "🚫 You need to be the **server owner** or have the **Architect role** to use this command.",
            ephemeral=True
        )
        return

    allowed, msg = can_moderate(interaction.user, user)
    if not allowed:
        await interaction.response.send_message(msg, ephemeral=True)
        return

    # Store warning
    guild_data = get_guild_data(interaction.guild.id)
    user_id = str(user.id)
    guild_data["warnings"].setdefault(user_id, [])
    warning = {
        "reason": reason,
        "moderator_id": interaction.user.id,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    guild_data["warnings"][user_id].append(warning)
    save_mod_data(mod_data)

    warning_count = len(guild_data["warnings"][user_id])

    embed = create_embed(
        title="⚠️ User Warned",
        description=f"**User:** {user.mention}\n**Reason:** {reason}\n"
                    f"**Total warnings:** {warning_count}\n**Moderator:** {interaction.user.mention}",
        color=discord.Color.orange()
    )
    await interaction.response.send_message(embed=embed)

    # DM the user
    dm_embed = create_embed(
        title=f"⚠️ You were warned in {interaction.guild.name}",
        description=f"**Reason:** {reason}\n"
                    f"**Total warnings:** {warning_count}\n"
                    f"**Moderator:** {interaction.user.name}",
        color=discord.Color.orange()
    )
    await try_dm_user(user, dm_embed)

    # Log it
    log_embed = create_embed(
        title="⚠️ Warn",
        description=f"**User:** {user.mention} (`{user.id}`)\n"
                    f"**Reason:** {reason}\n"
                    f"**Warnings now:** {warning_count}\n"
                    f"**Moderator:** {interaction.user.mention}",
        color=discord.Color.orange()
    )
    await send_mod_log(interaction.guild, log_embed)


# ---- /warnings ----
@bot.tree.command(name="warnings", description="List warnings for a user (defaults to yourself)")
@app_commands.describe(user="The user to check (defaults to you)")
async def slash_warnings(interaction: discord.Interaction, user: discord.Member = None):
    user = user or interaction.user
    guild_data = get_guild_data(interaction.guild.id)
    warnings = guild_data["warnings"].get(str(user.id), [])

    embed = create_embed(
        title=f"📋 Warnings for {user.display_name}",
        description=f"**Total warnings:** {len(warnings)}"
    )
    embed.set_thumbnail(url=user.display_avatar.url)

    if not warnings:
        embed.description += "\n✨ No warnings on record. Clean slate!"
    else:
        # Show up to 10 most recent
        for i, w in enumerate(warnings[-10:], 1):
            try:
                mod_user = await interaction.guild.fetch_member(w["moderator_id"])
                mod_str = mod_user.mention
            except (discord.NotFound, discord.HTTPException):
                mod_str = f"<@{w['moderator_id']}>"
            ts = w["timestamp"][:19].replace("T", " ")
            embed.add_field(
                name=f"#{i} — {ts}",
                value=f"**Reason:** {w['reason']}\n**By:** {mod_str}",
                inline=False
            )
        if len(warnings) > 10:
            embed.set_footer(text=f"AI Friend Bot v4.0 • Showing last 10 of {len(warnings)}")
    await interaction.response.send_message(embed=embed)


# ---- /clearwarnings ----
@bot.tree.command(name="clearwarnings", description="Clear all warnings for a user")
@app_commands.describe(user="The user whose warnings to clear", reason="Reason for clearing")
async def slash_clearwarnings(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    if not has_mod_access(interaction.user):
        await interaction.response.send_message(
            "🚫 You need to be the **server owner** or have the **Architect role** to use this command.",
            ephemeral=True
        )
        return

    allowed, msg = can_moderate(interaction.user, user)
    if not allowed:
        await interaction.response.send_message(msg, ephemeral=True)
        return

    guild_data = get_guild_data(interaction.guild.id)
    user_id = str(user.id)
    cleared_count = len(guild_data["warnings"].get(user_id, []))
    guild_data["warnings"][user_id] = []
    save_mod_data(mod_data)

    embed = create_embed(
        title="🧹 Warnings Cleared",
        description=f"Cleared **{cleared_count}** warning(s) for {user.mention}.\n"
                    f"**Reason:** {reason}\n**Moderator:** {interaction.user.mention}",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

    log_embed = create_embed(
        title="🧹 Warnings Cleared",
        description=f"**User:** {user.mention} (`{user.id}`)\n"
                    f"**Cleared:** {cleared_count} warning(s)\n"
                    f"**Reason:** {reason}\n"
                    f"**Moderator:** {interaction.user.mention}",
        color=discord.Color.green()
    )
    await send_mod_log(interaction.guild, log_embed)


# ---- /timeout ----
@bot.tree.command(name="timeout", description="Timeout a user for a specified duration")
@app_commands.describe(
    user="The user to timeout",
    duration="Duration (e.g., '30m', '2h', '1d', '1w')",
    reason="Reason for the timeout"
)
async def slash_timeout(interaction: discord.Interaction, user: discord.Member, duration: str, reason: str = "No reason provided"):
    if not has_mod_access(interaction.user):
        await interaction.response.send_message(
            "🚫 You need to be the **server owner** or have the **Architect role** to use this command.",
            ephemeral=True
        )
        return

    allowed, msg = can_moderate(interaction.user, user)
    if not allowed:
        await interaction.response.send_message(msg, ephemeral=True)
        return

    td = parse_duration(duration)
    if not td:
        await interaction.response.send_message(
            f"❌ Invalid duration `{duration}`.\n"
            f"💡 Use formats like: `30m`, `2h`, `1d`, `1w` (max 28 days).",
            ephemeral=True
        )
        return

    if td > datetime.timedelta(days=28):
        await interaction.response.send_message(
            "❌ Discord's maximum timeout is **28 days**.",
            ephemeral=True
        )
        return

    until = datetime.datetime.now(datetime.timezone.utc) + td

    try:
        await user.timeout(until, reason=reason)
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I don't have permission to timeout users.\n"
            "💡 Check that my role has **Moderate Members** permission.",
            ephemeral=True
        )
        return
    except discord.HTTPException as e:
        await interaction.response.send_message(f"❌ Failed to timeout: {e}", ephemeral=True)
        return

    embed = create_embed(
        title="⏱️ User Timed Out",
        description=f"**User:** {user.mention}\n"
                    f"**Duration:** {format_timedelta(td)}\n"
                    f"**Expires:** <t:{int(until.timestamp())}:R>\n"
                    f"**Reason:** {reason}\n"
                    f"**Moderator:** {interaction.user.mention}",
        color=discord.Color.orange()
    )
    await interaction.response.send_message(embed=embed)

    dm_embed = create_embed(
        title=f"⏱️ You were timed out in {interaction.guild.name}",
        description=f"**Duration:** {format_timedelta(td)}\n"
                    f"**Expires:** <t:{int(until.timestamp())}:R>\n"
                    f"**Reason:** {reason}",
        color=discord.Color.orange()
    )
    await try_dm_user(user, dm_embed)

    log_embed = create_embed(
        title="⏱️ Timeout",
        description=f"**User:** {user.mention} (`{user.id}`)\n"
                    f"**Duration:** {format_timedelta(td)}\n"
                    f"**Expires:** <t:{int(until.timestamp())}:F>\n"
                    f"**Reason:** {reason}\n"
                    f"**Moderator:** {interaction.user.mention}",
        color=discord.Color.orange()
    )
    await send_mod_log(interaction.guild, log_embed)


# ---- /untimeout ----
@bot.tree.command(name="untimeout", description="Remove a timeout from a user")
@app_commands.describe(user="The user to remove timeout from", reason="Reason for removing timeout")
async def slash_untimeout(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    if not has_mod_access(interaction.user):
        await interaction.response.send_message(
            "🚫 You need to be the **server owner** or have the **Architect role** to use this command.",
            ephemeral=True
        )
        return

    allowed, msg = can_moderate(interaction.user, user)
    if not allowed:
        await interaction.response.send_message(msg, ephemeral=True)
        return

    if user.timed_out_until is None:
        await interaction.response.send_message(
            f"❌ {user.mention} is not currently timed out.",
            ephemeral=True
        )
        return

    try:
        await user.timeout(None, reason=reason)
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I don't have permission to remove timeouts.",
            ephemeral=True
        )
        return
    except discord.HTTPException as e:
        await interaction.response.send_message(f"❌ Failed to remove timeout: {e}", ephemeral=True)
        return

    embed = create_embed(
        title="✅ Timeout Removed",
        description=f"**User:** {user.mention}\n"
                    f"**Reason:** {reason}\n"
                    f"**Moderator:** {interaction.user.mention}",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

    log_embed = create_embed(
        title="✅ Timeout Removed",
        description=f"**User:** {user.mention} (`{user.id}`)\n"
                    f"**Reason:** {reason}\n"
                    f"**Moderator:** {interaction.user.mention}",
        color=discord.Color.green()
    )
    await send_mod_log(interaction.guild, log_embed)


# ---- /kick ----
@bot.tree.command(name="kick", description="Kick a user from the server")
@app_commands.describe(user="The user to kick", reason="Reason for the kick")
async def slash_kick(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    if not has_mod_access(interaction.user):
        await interaction.response.send_message(
            "🚫 You need to be the **server owner** or have the **Architect role** to use this command.",
            ephemeral=True
        )
        return

    allowed, msg = can_moderate(interaction.user, user)
    if not allowed:
        await interaction.response.send_message(msg, ephemeral=True)
        return

    # DM before kick (user is still in the guild)
    dm_embed = create_embed(
        title=f"👢 You were kicked from {interaction.guild.name}",
        description=f"**Reason:** {reason}\n"
                    f"You can rejoin with a valid invite link.",
        color=discord.Color.red()
    )
    await try_dm_user(user, dm_embed)

    try:
        await user.kick(reason=reason)
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I don't have permission to kick members.\n"
            "💡 Check that my role has **Kick Members** permission.",
            ephemeral=True
        )
        return
    except discord.HTTPException as e:
        await interaction.response.send_message(f"❌ Failed to kick: {e}", ephemeral=True)
        return

    embed = create_embed(
        title="👢 User Kicked",
        description=f"**User:** {user.mention} (`{user.id}`)\n"
                    f"**Reason:** {reason}\n"
                    f"**Moderator:** {interaction.user.mention}",
        color=discord.Color.red()
    )
    await interaction.response.send_message(embed=embed)

    log_embed = create_embed(
        title="👢 Kick",
        description=f"**User:** {user.mention} (`{user.id}`)\n"
                    f"**Reason:** {reason}\n"
                    f"**Moderator:** {interaction.user.mention}",
        color=discord.Color.red()
    )
    await send_mod_log(interaction.guild, log_embed)


# ---- /ban ----
@bot.tree.command(name="ban", description="Ban a user from the server")
@app_commands.describe(
    user="The user to ban",
    days="Days of message history to delete (0-7, default 0)",
    reason="Reason for the ban"
)
async def slash_ban(interaction: discord.Interaction, user: discord.Member, days: int = 0, reason: str = "No reason provided"):
    if not has_mod_access(interaction.user):
        await interaction.response.send_message(
            "🚫 You need to be the **server owner** or have the **Architect role** to use this command.",
            ephemeral=True
        )
        return

    allowed, msg = can_moderate(interaction.user, user)
    if not allowed:
        await interaction.response.send_message(msg, ephemeral=True)
        return

    if days < 0 or days > 7:
        await interaction.response.send_message(
            "❌ `days` must be between 0 and 7.",
            ephemeral=True
        )
        return

    # DM before ban
    dm_embed = create_embed(
        title=f"🔨 You were banned from {interaction.guild.name}",
        description=f"**Reason:** {reason}",
        color=discord.Color.dark_red()
    )
    await try_dm_user(user, dm_embed)

    try:
        await user.ban(delete_message_days=days, reason=reason)
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I don't have permission to ban members.\n"
            "💡 Check that my role has **Ban Members** permission.",
            ephemeral=True
        )
        return
    except discord.HTTPException as e:
        await interaction.response.send_message(f"❌ Failed to ban: {e}", ephemeral=True)
        return

    embed = create_embed(
        title="🔨 User Banned",
        description=f"**User:** {user.mention} (`{user.id}`)\n"
                    f"**Reason:** {reason}\n"
                    f"**History deleted:** {days} day(s)\n"
                    f"**Moderator:** {interaction.user.mention}",
        color=discord.Color.dark_red()
    )
    await interaction.response.send_message(embed=embed)

    log_embed = create_embed(
        title="🔨 Ban",
        description=f"**User:** {user.mention} (`{user.id}`)\n"
                    f"**Reason:** {reason}\n"
                    f"**History deleted:** {days} day(s)\n"
                    f"**Moderator:** {interaction.user.mention}",
        color=discord.Color.dark_red()
    )
    await send_mod_log(interaction.guild, log_embed)


# ---- /unban ----
@bot.tree.command(name="unban", description="Unban a user by their ID")
@app_commands.describe(user_id="The ID of the user to unban", reason="Reason for the unban")
async def slash_unban(interaction: discord.Interaction, user_id: str, reason: str = "No reason provided"):
    if not has_mod_access(interaction.user):
        await interaction.response.send_message(
            "🚫 You need to be **server owner** or have the **Architect role** to use this command.",
            ephemeral=True
        )
        return

    # Validate ID
    try:
        uid = int(user_id)
    except ValueError:
        await interaction.response.send_message(
            "❌ Invalid user ID. Must be a numeric Discord user ID.",
            ephemeral=True
        )
        return

    # Check if banned
    try:
        await interaction.guild.fetch_ban(discord.Object(id=uid))
    except discord.NotFound:
        await interaction.response.send_message(
            f"❌ User with ID `{uid}` is not banned.",
            ephemeral=True
        )
        return
    except discord.HTTPException as e:
        await interaction.response.send_message(f"❌ Failed to check ban: {e}", ephemeral=True)
        return

    try:
        await interaction.guild.unban(discord.Object(id=uid), reason=reason)
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I don't have permission to unban members.",
            ephemeral=True
        )
        return
    except discord.HTTPException as e:
        await interaction.response.send_message(f"❌ Failed to unban: {e}", ephemeral=True)
        return

    embed = create_embed(
        title="✅ User Unbanned",
        description=f"**User ID:** `{uid}`\n"
                    f"**Reason:** {reason}\n"
                    f"**Moderator:** {interaction.user.mention}",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

    log_embed = create_embed(
        title="✅ Unban",
        description=f"**User ID:** `{uid}`\n"
                    f"**Reason:** {reason}\n"
                    f"**Moderator:** {interaction.user.mention}",
        color=discord.Color.green()
    )
    await send_mod_log(interaction.guild, log_embed)


# ---- /purge ----
@bot.tree.command(name="purge", description="Bulk delete messages (optionally from a specific user)")
@app_commands.describe(
    amount="Number of messages to delete (1-100)",
    user="Optional: only delete messages from this user"
)
async def slash_purge(interaction: discord.Interaction, amount: int, user: discord.Member = None):
    if not has_mod_access(interaction.user):
        await interaction.response.send_message(
            "🚫 You need to be the **server owner** or have the **Architect role** to use this command.",
            ephemeral=True
        )
        return

    if amount < 1 or amount > 100:
        await interaction.response.send_message(
            "❌ Amount must be between 1 and 100.",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    def check(msg):
        if user:
            return msg.author.id == user.id
        return True

    try:
        # +1 to account for the command message itself
        deleted = await interaction.channel.purge(limit=amount + 1, check=check)
        # Subtract 1 because the command message is included
        actual_deleted = len(deleted) - 1
    except discord.Forbidden:
        await interaction.followup.send(
            "❌ I don't have permission to manage messages here.\n"
            "💡 Check that I have **Manage Messages** permission.",
            ephemeral=True
        )
        return
    except discord.HTTPException as e:
        await interaction.followup.send(f"❌ Failed to purge: {e}", ephemeral=True)
        return

    target_str = f" from {user.mention}" if user else ""
    await interaction.followup.send(
        f"✅ Deleted **{actual_deleted}** message(s){target_str}.",
        ephemeral=True
    )

    log_embed = create_embed(
        title="🧹 Purge",
        description=f"**Channel:** {interaction.channel.mention}\n"
                    f"**Messages deleted:** {actual_deleted}\n"
                    f"**Filter:** {user.mention if user else 'All users'}\n"
                    f"**Moderator:** {interaction.user.mention}",
        color=discord.Color.blue()
    )
    await send_mod_log(interaction.guild, log_embed)


# ==========================================================
# GLOBAL ERROR HANDLERS
# ==========================================================

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    send_method = interaction.followup.send if interaction.response.is_done() else interaction.response.send_message

    if isinstance(error, app_commands.MissingPermissions):
        await send_method("🚫 You don't have permission to use this command.", ephemeral=True)
    elif isinstance(error, app_commands.MissingRequiredArgument):
        await send_method(f"❌ Missing required argument: `{error.param.name}`", ephemeral=True)
    elif isinstance(error, app_commands.BadArgument):
        await send_method("❌ Invalid argument provided.", ephemeral=True)
    elif isinstance(error, app_commands.CommandOnCooldown):
        await send_method(f"⏳ This command is on cooldown. Try again in {error.retry_after:.1f}s", ephemeral=True)
    elif isinstance(error, app_commands.BotMissingPermissions):
        missing = ", ".join(error.missing_permissions)
        await send_method(
            f"❌ I'm missing permissions: **{missing}**\n"
            f"💡 Check my role's permissions in Server Settings → Roles.",
            ephemeral=True
        )
    else:
        await send_method(f"❌ An error occurred: {error}", ephemeral=True)


# ==========================
# RUN
# ==========================

bot.run(TOKEN)
