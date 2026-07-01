# 🛡️ AI Friend Bot v4.0 — Moderation System Guide

A complete guide to setting up, configuring, and using the moderation features in AI Friend Bot v4.0.

---

## 📖 Table of Contents

1. [Overview](#overview)
2. [First-Time Setup](#first-time-setup)
3. [Permission Requirements](#permission-requirements)
4. [Configuration Commands](#configuration-commands)
5. [Moderation Commands Reference](#moderation-commands-reference)
6. [Security Model](#security-model)
7. [Data Storage](#data-storage)
8. [Logging System](#logging-system)
9. [Duration Format](#duration-format)
10. [Troubleshooting](#troubleshooting)
11. [Best Practices](#best-practices)

---

## Overview

The moderation system provides Discord server moderation through slash commands, with a 4-layer security model:

| Feature | Status |
|---|---|
| Slash commands only | ✅ |
| Architect role system | ✅ |
| Hierarchical permissions | ✅ |
| Persistent warnings | ✅ |
| Mod log channel | ✅ |
| User DM notifications | ✅ |
| Audit trail | ✅ |

### What's Protected Against

- 🚫 Server owner being moderated
- 🚫 The bot itself being moderated
- 🚫 Users with equal or higher roles
- 🚫 Unauthorized access (non-Architect/non-Owner)

---

## First-Time Setup

Follow these steps **in order** to enable moderation in your server.

### Step 1: Set Up Bot Permissions

1. Go to **Server Settings → Roles**
2. Find your bot's role (e.g., `AI Friend Bot`)
3. Enable these permissions:
   - ✅ **Manage Messages** (for `/purge`)
   - ✅ **Kick Members** (for `/kick`)
   - ✅ **Ban Members** (for `/ban` and `/unban`)
   - ✅ **Moderate Members** (for `/timeout` and `/untimeout`)
   - ✅ **Send Messages** (in your mod log channel)
   - ✅ **Embed Links** (for rich log messages)
4. Drag the bot role **above** member roles in the role list
   - The bot cannot moderate users with roles higher than its own

### Step 2: Create a Mod Log Channel (Optional but Recommended)

1. Create a new channel, e.g., `#mod-logs`
2. Set permissions:
   - ✅ Bot can view, send messages, embed links
   - ❌ Regular members **cannot** see it (or use a private channel)
3. The channel ID will be needed for `/setlog`

### Step 3: Create an Architect Role (Optional but Recommended)

If you want a separate group (besides the owner) to moderate:

1. Go to **Server Settings → Roles → Create Role**
2. Name it `Architect` (or `Moderator`, `Staff`, etc.)
3. Give it a distinctive color
4. **Don't** give it any extra Discord permissions — access is controlled by the bot
5. Assign the role to trusted staff members

> 💡 **Alternative:** Skip this step. The server owner can moderate directly without any role.

### Step 4: Run Configuration Commands

As the **server owner**, run these in any channel:

```
/setarchitect @Architect
/setlog #mod-logs
```

You'll see green confirmation embeds for each.

### Step 5: Verify Setup

Have an Architect try:
```
/ping
```

If it works, the role is correctly configured.

---

## Permission Requirements

### Bot Permissions (in Server Settings)

| Permission | Used By | Why |
|---|---|---|
| Manage Messages | `/purge` | Delete messages in bulk |
| Kick Members | `/kick` | Remove members from server |
| Ban Members | `/ban`, `/unban` | Ban/unban members |
| Moderate Members | `/timeout`, `/untimeout` | Apply/remove timeouts |
| Send Messages | All commands | Send responses |
| Embed Links | All commands | Display rich embeds |
| View Channels | All commands | See channels |

### User Permissions (to Use Mod Commands)

| User Type | Can Use Mod Commands? |
|---|---|
| Server Owner | ✅ Always |
| Architect Role Holders | ✅ After `/setarchitect` |
| Users with Administrator permission | ❌ **No** — only Architect role works |
| Regular Members | ❌ No |

> ⚠️ **Important:** The "Administrator" Discord permission does **not** grant moderation access. Only the **Architect role** (or being the owner) does.

---

## Configuration Commands

These are **owner-only** commands for setting up the system.

### `/setarchitect @role`

Sets which role can use moderation commands.

**Usage:**
```
/setarchitect @Moderator
```

**Requirements:**
- Must be the **server owner**
- The role must exist in the server

**What it does:**
- Stores the role ID in `data/moderation.json`
- Server owner always has access regardless of roles
- Only **one** Architect role per server

### `/setlog #channel`

Sets the channel where all moderation actions are logged.

**Usage:**
```
/setlog #mod-logs
```

**Requirements:**
- Must be the **server owner**
- Bot must have `Send Messages` permission in the channel

**What it does:**
- Every `/warn`, `/kick`, `/ban`, etc. sends a log embed to this channel
- If not set, actions still work — they're just not logged anywhere
- Log messages include the moderator, target, reason, and timestamp

---

## Moderation Commands Reference

All commands require **Owner or Architect** role.

### `/warn @user [reason]`

Issues a warning to a user. Warnings persist in `data/moderation.json`.

**Examples:**
```
/warn @user Spamming in #general
/warn @user
/warn @user Inappropriate language in #off-topic
```

**Output:**
- ⚠️ Embed showing user, reason, total warnings, and moderator
- DM sent to the user (if DMs are open)
- Log entry in mod log channel

### `/warnings [@user]`

Lists all warnings for a user. Defaults to yourself.

**Examples:**
```
/warnings                  # Your own warnings
/warnings @troublemaker    # Another user's warnings
```

**Output:**
- 📋 Embed showing up to 10 most recent warnings
- Each warning has reason, moderator, and timestamp
- Shows total count

### `/clearwarnings @user [reason]`

Removes all warnings for a user.

**Examples:**
```
/clearwarnings @user
/clearwarnings @user Appeal accepted - cleaned slate
```

**Output:**
- 🧹 Embed showing cleared count and reason
- Log entry with the reason

### `/timeout @user <duration> [reason]`

Temporarily prevents a user from sending messages, reacting, or joining voice.

**Duration Format:** See [Duration Format](#duration-format) section.

**Examples:**
```
/timeout @user 30m Spamming
/timeout @user 2h Excessive caps
/timeout @user 1d Raid attempt
/timeout @user 1w Cooling off
```

**Limits:**
- Maximum: **28 days** (Discord limit)
- Minimum: 1 second

**What happens:**
- User cannot send messages, add reactions, join voice, or use slash commands
- They CAN still read messages
- Auto-expires after the duration
- User is DM'd with the reason and expiration time

### `/untimeout @user [reason]`

Manually removes a timeout from a user.

**Examples:**
```
/untimeout @user
/untimeout @user Apologized - giving another chance
```

**Output:**
- ✅ Embed confirming removal
- Log entry

### `/kick @user [reason]`

Removes a user from the server. They can rejoin with an invite.

**Examples:**
```
/kick @user Disruptive behavior
/kick @user
```

**What happens:**
- User is DM'd with the reason (if possible)
- User is removed from the server
- Their messages remain
- Log entry created

### `/ban @user [days] [reason]`

Permanently bans a user from the server.

**Parameters:**
- `user` — The user to ban
- `days` — How many days of message history to delete (0–7, default 0)
- `reason` — Why they're being banned

**Examples:**
```
/ban @user
/ban @user 7 Spam raid
/ban @user 1 Repeated rule violations after warnings
/ban @user 0 Compromised account
```

**Limits:**
- `days` must be **0–7** (Discord limit)

**What happens:**
- User is DM'd with the reason
- User is removed from the server
- Optionally deletes their recent message history
- Log entry created

### `/unban <user_id> [reason]`

Removes a ban by user ID. Useful when the banned user is no longer in the server.

**How to get a user ID:**
1. Enable Developer Mode in Discord (Settings → Advanced → Developer Mode)
2. Right-click the user's profile → Copy User ID
3. Or check the mod log embed for the ID

**Examples:**
```
/unban 123456789012345678
/unban 123456789012345678 Appealed and accepted
```

**Output:**
- ✅ Embed confirming unban
- Log entry

### `/purge <amount> [user]`

Bulk deletes messages from the current channel.

**Parameters:**
- `amount` — How many messages to delete (1–100)
- `user` — Optional filter to only delete messages from a specific user

**Examples:**
```
/purge 50                  # Delete last 50 messages
/purge 20 @spammer         # Delete last 20 messages from @spammer
/purge 100                 # Maximum bulk delete
```

**Limits:**
- 1–100 messages per command
- Only deletes messages under **14 days old** (Discord limit)

**What happens:**
- Deletes the specified number of messages (plus the command message)
- Ephemeral response (only you see the confirmation)
- Log entry in mod log

---

## Security Model

The bot uses a **4-layer security check** before executing any mod action.

### Layer 1: Authentication

```
Is the user the server owner?
   OR
Does the user have the Architect role?
```

If neither, the command is rejected.

### Layer 2: Owner Protection

```
Is the target the server owner?
   → Reject: "Cannot moderate the server owner."
```

### Layer 3: Self-Protection

```
Is the target the bot itself?
   → Reject: "Cannot moderate myself."
```

### Layer 4: Role Hierarchy

```
Is the target's top role >= the actor's top role?
   → Reject: "You cannot moderate {user} — they have an equal or higher role."
```

### Layer 4b: Bot Role Check

```
Is the target's top role >= the bot's top role?
   → Reject: "I cannot moderate {user} — move my role above theirs."
```

This prevents the bot from being used to attack members with higher roles.

---

## Data Storage

All moderation data is stored in **`data/moderation.json`**.

### File Location

```
📦 Project Root
 ├── bot.py
 ├── .env
 ├── data/
 │    └── moderation.json   ← Auto-created
```

### File Structure

```json
{
  "123456789012345678": {
    "architect_role_id": 987654321098765432,
    "log_channel_id": 555555555555555555,
    "warnings": {
      "111111111111111111": [
        {
          "reason": "Spamming in #general",
          "moderator_id": 222222222222222222,
          "timestamp": "2026-07-01T19:45:00+00:00"
        },
        {
          "reason": "Inappropriate language",
          "moderator_id": 222222222222222222,
          "timestamp": "2026-07-01T20:15:00+00:00"
        }
      ]
    }
  }
}
```

### Key Details

- **Per-guild isolation** — Each server has its own data
- **Saved immediately** — Every change is written to disk instantly
- **No database needed** — Pure JSON file
- **Easily backupable** — Just copy `data/moderation.json`
- **Survives bot restarts** — Data persists across reboots

### Backup Recommendations

```bash
# Manual backup
cp data/moderation.json data/moderation.backup.json

# Automated daily backup (cron)
0 0 * * * cp /path/to/data/moderation.json /backup/moderation.$(date +\%F).json
```

### Resetting Data

To completely reset mod data for a server:
1. Stop the bot
2. Edit `data/moderation.json` and remove the guild's entry
3. Restart the bot

---

## Logging System

When `/setlog` is configured, **every mod action** sends an embed to that channel.

### Log Format Examples

#### Warn Log
```
⚠️ Warn
─────────────────────────
User: @spammer (123456789)
Reason: Spamming in #general
Warnings now: 3
Moderator: @Architect
─────────────────────────
AI Friend Bot v4.0 • 2026-07-01 19:45
```

#### Ban Log
```
🔨 Ban
─────────────────────────
User: @raider (123456789)
Reason: Raid attempt
History deleted: 7 day(s)
Moderator: @Architect
─────────────────────────
AI Friend Bot v4.0 • 2026-07-01 20:00
```

#### Purge Log
```
🧹 Purge
─────────────────────────
Channel: #general
Messages deleted: 50
Filter: @spammer
Moderator: @Architect
─────────────────────────
AI Friend Bot v4.0 • 2026-07-01 20:15
```

### Log Channel Tips

- Use a **private channel** visible only to staff
- Pin important log messages
- Consider using a Discord webhook for external archiving
- Search the channel for user IDs to find all actions on a user

---

## Duration Format

For `/timeout`, use these formats:

| Format | Meaning | Example |
|---|---|---|
| `Ns` | N seconds | `30s` |
| `Nm` | N minutes | `15m` |
| `Nh` | N hours | `2h` |
| `Nd` | N days | `1d` |
| `Nw` | N weeks | `1w` |

### Examples

```
/timeout @user 30s   # 30 seconds (testing only)
/timeout @user 5m    # 5 minutes
/timeout @user 30m   # 30 minutes
/timeout @user 1h    # 1 hour
/timeout @user 12h   # 12 hours
/timeout @user 1d    # 1 day
/timeout @user 7d    # 1 week
/timeout @user 4w    # 4 weeks (max)
```

### Limits

- **Minimum:** 1 second
- **Maximum:** 28 days (`4w` or `28d`)
- Anything beyond 28 days will be rejected

### Tips

- Use `30m` or `1h` for minor infractions
- Use `1d` for serious first offenses
- Use `1w` or longer for repeated issues
- Use `4w` (max) for severe cases before considering a ban

---

## Troubleshooting

### "I don't have permission" when using mod commands

**Cause:** You're not the server owner or don't have the Architect role.

**Solution:**
- Server owner: nothing to do, you have access
- Other users: ask the owner to run `/setarchitect @YourRole`

### "Cannot moderate {user} — they have an equal or higher role"

**Cause:** The target's highest role is at or above your highest role.

**Solution:** Have someone with a higher role perform the action, or ask the target to step down.

### "I cannot moderate {user} — their role is higher than mine"

**Cause:** The bot's role is below the target's role in the role list.

**Solution:**
1. Go to Server Settings → Roles
2. Drag the bot's role **above** the target's role
3. Try the command again

### "I'm missing permissions" error from the bot

**Cause:** The bot doesn't have the required Discord permission.

**Solution:**
1. Server Settings → Roles → Bot's role
2. Enable the permission mentioned in the error
3. Common ones: `Kick Members`, `Ban Members`, `Moderate Members`, `Manage Messages`

### Messages over 14 days old won't delete

**Cause:** Discord limits bulk deletion to messages under 14 days old.

**Solution:**
- For older messages, delete them manually one by one
- Or use a dedicated moderation bot like `MEE6` or `Dyno` for this case

### "Failed to unban: Not Found"

**Cause:** The user ID is correct, but the user isn't actually banned.

**Solution:** Double-check the ID. You can use Discord's "Bans" tab in Server Settings to see the list of banned users and their IDs.

### User didn't receive a DM

**Cause:** The user has DMs disabled, or has the bot blocked.

**Solution:** This is normal and not an error. The mod action still works. Check the mod log to confirm.

### Architect role got deleted

**Cause:** The role was deleted from the server.

**Solution:** Re-create the role and run `/setarchitect @NewRole` again.

### Mod data file is corrupted

**Cause:** Manual editing error, or the bot was killed mid-write.

**Solution:**
1. Stop the bot
2. Restore from backup if you have one
3. Or delete `data/moderation.json` (this loses all warnings and reverts to defaults)
4. Re-run `/setarchitect` and `/setlog`

### Slash commands not appearing

**Cause:** Discord caches slash commands; updates can take up to 1 hour globally.

**Solution:**
- Wait up to 1 hour for global sync
- Or restart Discord (`Ctrl+R`)
- Or kick and re-invite the bot (forces a fresh sync)

---

## Best Practices

### 🏗️ Setup

1. **Create a dedicated mod log channel** — private, only visible to staff
2. **Use a clear Architect role name** — `Moderator`, `Staff`, `Architect`
3. **Don't give Architect role too many people** — only trusted staff
4. **Backup `data/moderation.json` regularly** — it's your only record of warnings

### 📝 Moderation

1. **Always include a reason** — even a short one helps track patterns
2. **Warn before timeout, timeout before ban** — progressive discipline
3. **Use `/warnings` before deciding** — check if it's a repeat offense
4. **Be consistent** — same rule → same action for everyone
5. **Document in mod log** — if you have a complex situation, post details

### ⏱️ Timeouts

| Offense Severity | Recommended Duration |
|---|---|
| First minor infraction | `15m` to `1h` |
| Repeated minor | `2h` to `12h` |
| Major rule break | `1d` to `3d` |
| Severe / repeat offender | `1w` to `4w` (max) |
| Raid / extreme | Ban instead |

### 🔨 When to Ban vs Kick

| Use **Kick** When | Use **Ban** When |
|---|---|
| First-time serious issue | Repeated rule violations |
| User seems genuine but made a mistake | Account is clearly a troll/alt |
| You want to give them a second chance | User is evading previous bans |
| User appealed and you want to reset | User is a clear security threat |

### 🛡️ Security

1. **Never share your `.env` file** — it contains the bot token
2. **Limit Architect assignments** — fewer people = more accountable
3. **Review mod logs regularly** — catch any abuse early
4. **Don't ban for disagreements** — mod actions should be rule-based
5. **Have a public appeals process** — let users request `/unban` via tickets

### 💾 Data Safety

1. **Backup weekly** at minimum
2. **Use Git** to track `bot.py` (but **not** `data/moderation.json` if it contains user IDs you want to keep private)
3. **Test mod commands in a private test server** before deploying to your main one

### 🎯 For Multi-Server Use

Each server has **independent**:
- Architect role
- Log channel
- Warning database

This means a user warned in Server A has **no warnings** in Server B.

---

## 📞 Quick Reference

### Setup (Owner)
```
/setarchitect @role
/setlog #channel
```

### Warn Flow
```
/warn @user reason
/warnings @user
/clearwarnings @user
```

### Escalation Flow
```
/warn @user           # 1st offense
/timeout @user 1h     # 2nd offense
/timeout @user 1d     # 3rd offense
/kick @user           # 4th offense
/ban @user 7          # 5th offense
```

### Cleanup
```
/purge 50             # Delete last 50 messages
/purge 20 @spammer    # Delete 20 from a user
```

---

## 🔗 Related Documentation

- **README.md** — Project overview and quick start
- **bot.py** — Source code (well-commented)
- **CHANGELOG.md** — Version history *(coming soon)*

---

**Need more help?** Check the source code in `bot.py` — all commands have inline comments explaining their behavior.

*Last updated: AI Friend Bot v4.0*
