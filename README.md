# Minecraft Server

Paper 1.21.11 production server with Telegram notifications and auto backups.

## Setup (5 minutes)

```bash
# 1. Clone repo
git clone https://github.com/TrueSurvival/server.git /opt/minecraft
cd /opt/minecraft

# 2. Setup environment
cp .env.example .env
# Edit .env with your Telegram token, RCON password, etc.

# 3. Start server
sudo systemctl start minecraft mc-tgbridge mc-web afk-bot afk-bot2

# 4. Check status
sudo systemctl status minecraft
```

## What's Running

| Service | What it does | Port |
|---------|-------------|------|
| minecraft | Game server | 25565 |
| mc-tgbridge | Telegram notifications | - |
| mc-web | Web dashboard | 8090 |
| afk-bot | Anti-AFK bot | 25565 |
| afk-bot2 | Anti-AFK bot #2 | 25565 |

## Files & Folders

```
server-2/          - Game world and server configs
backups/           - Daily backups (auto at 3 AM)
afk-bot/           - Bot code
web/               - Web dashboard (http://localhost:8090)
api_server.py      - Stats API
tg_bridge.py       - Telegram integration
backup.sh          - Backup script
.env               - Your credentials (don't commit this)
```

## Configure

Edit `.env`:
```
TG_TOKEN=your_bot_token
TG_CHAT_ID=your_forum_id
RCON_PASSWORD=server_rcon_password
BOT_NAME=AFKBot
BOT_PASSWORD=bot_password
```

## Logs & Monitoring

```bash
# Server logs
tail -f server-2/logs/latest.log

# Telegram bridge status
sudo journalctl -u mc-tgbridge -f

# Bot status
ps aux | grep afk-bot
```

## Backup

```bash
# Manual backup
bash backup.sh

# View backups
ls -lh backups/

# Restore (extract and replace server-2)
unzip backups/minecraft-2026-06-10_03-00-01.zip
```

## Web Dashboard

Open http://localhost:8090 to see:
- Online players
- Server stats (TPS, memory)
- World info
- Live logs

## Players & Whitelist

Add players to `server-2/whitelist.json`:
```json
[
  {"name": "PlayerName", "uuid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}
]
```

## Troubleshooting

**Server won't start**
```bash
sudo journalctl -u minecraft -n 50
# Check: java -version
# Check port: sudo netstat -tlnp | grep 25565
```

**Bots not joining**
```bash
cat server-2/whitelist.json | grep -i afk
# Re-add: /whitelist add AFKBot
```

**Telegram not working**
```bash
# Test: curl https://api.telegram.org/bot{YOUR_TOKEN}/getMe
```

**Backup failed**
```bash
bash backup.sh
# Or check: rclone ls gdrive:minecraft-backups/
```

## Performance

- World: 1.6 GB
- Backups: 338 MB each
- Memory: 8-10 GB
- TPS: 20.0 (no lag)

## More Info

- **CLONE_GUIDE.md** - Full deployment steps
- **CLONE_QUICK_COMMANDS.md** - Bash reference
- **AUDIT_REPORT.txt** - Complete infrastructure audit

---

Last updated: June 10, 2026 | Status: Running
