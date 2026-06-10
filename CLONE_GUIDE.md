# 🎮 Minecraft Server Clone Guide
**Current Server Size:** ~3.5GB total

## ✅ PRE-CLONE CHECKLIST

### 1. **Critical Files to Copy**
```
/opt/minecraft/.env                    # Main config (TG token, RCON, web port, etc.)
/opt/minecraft/setup.sh                # Setup automation
/opt/minecraft/backup.sh               # Backup script
/opt/minecraft/tg_bridge.py            # Telegram bot bridge
/opt/minecraft/web_server.py           # Web portal server
/opt/minecraft/api_server.py           # API server
/opt/minecraft/afk-bot/afk-bot.js      # AFKBot script
/opt/minecraft/afk-bot/package.json    # AFKBot dependencies
/opt/minecraft/afk-bot/.env            # AFKBot config
/opt/minecraft/afk-bot2/afk-bot.js     # AFKBot2 script
/opt/minecraft/afk-bot2/package.json   # AFKBot2 dependencies
/opt/minecraft/afk-bot2/.env           # AFKBot2 config
/opt/minecraft/web/                    # Web portal assets (HTML/CSS/JS)
```

### 2. **Server Data Files**
```
/opt/minecraft/server-2/world/                # Main world (keep for restore)
/opt/minecraft/server-2/config/               # Spigot config
/opt/minecraft/server-2/server.properties     # Server settings
/opt/minecraft/server-2/whitelist.json        # Whitelisted players
/opt/minecraft/server-2/ops.json              # Operators
/opt/minecraft/server-2/eula.txt              # EULA acceptance
/opt/minecraft/server-2/usercache.json        # Player cache
```

### 3. **Node.js & Dependencies**
```
/opt/minecraft/node/                   # Node.js binary (pre-compiled)
/opt/minecraft/afk-bot/node_modules/   # mineflayer, pathfinder deps
/opt/minecraft/afk-bot2/node_modules/  # AFKBot2 deps
```

### 4. **Systemd Services** (Create on new server)
```
/etc/systemd/system/minecraft.service          # Minecraft server
/etc/systemd/system/mc-tgbridge.service        # Telegram bridge
/etc/systemd/system/mc-web.service             # Web server
/etc/systemd/system/afk-bot.service            # AFKBot 1
/etc/systemd/system/afk-bot2.service           # AFKBot 2
/etc/systemd/system/minecraft-api.service      # API server
```

### 5. **Cron Jobs** (Create on new server)
```
/etc/cron.d/minecraft-backup                   # Daily 3 AM backup
```

---

## 🔧 CLONE PROCEDURE

### Step 1: Prepare Backup
```bash
# Create full backup
cd /opt/minecraft
tar czf /tmp/minecraft-clone-$(date +%Y%m%d).tar.gz \
  .env setup.sh backup.sh tg_bridge.py web_server.py api_server.py \
  afk-bot/afk-bot.js afk-bot/package.json afk-bot/.env afk-bot/node_modules \
  afk-bot2/afk-bot.js afk-bot2/package.json afk-bot2/.env afk-bot2/node_modules \
  server-2/world server-2/config server-2/server.properties \
  server-2/whitelist.json server-2/ops.json server-2/eula.txt \
  server-2/usercache.json web/ node/

# List created backup
ls -lh /tmp/minecraft-clone-*.tar.gz
```

### Step 2: Transfer to New Server
```bash
# Copy via rsync or SCP
rsync -avz /tmp/minecraft-clone-*.tar.gz newserver:/tmp/

# Or SCP
scp /tmp/minecraft-clone-*.tar.gz user@newserver:/tmp/
```

### Step 3: Extract on New Server
```bash
# Login to new server
ssh user@newserver

# Create directory
sudo mkdir -p /opt/minecraft

# Extract
cd /opt/minecraft
sudo tar xzf /tmp/minecraft-clone-*.tar.gz

# Fix permissions
sudo chown -R minecraft:minecraft /opt/minecraft
sudo chown -R www-data:www-data /opt/minecraft/web
```

### Step 4: Update Configuration
```bash
# Edit .env for new server (if needed)
nano /opt/minecraft/.env

# Key things to check:
# - RCON_PASSWORD (keep same or update)
# - WEB_PORT (8090 - same as nginx upstream)
# - TG_TOKEN (should be same)
# - BACKUP_REMOTE (keep gdrive path or update)
```

### Step 5: Install Dependencies
```bash
# Install Java, Python, rclone (if not present)
sudo apt update
sudo apt install -y openjdk-21-jre-headless python3 python3-pip python3-dotenv rclone
pip3 install mcrcon python-telegram-bot --break-system-packages

# Install Paper server (if not in backup)
cd /opt/minecraft/server-2
wget -q https://api.papermc.io/v2/projects/paper/versions/1.21.11/builds/131/downloads/paper-1.21.11-131.jar

# Install plugins (if not in backup)
mkdir -p /opt/minecraft/server-2/plugins
wget -q -O /opt/minecraft/server-2/plugins/AuthMe-6.0.0-Paper.jar \
  https://github.com/AuthMe/AuthMeReloaded/releases/download/5.6.0-beta/AuthMe-6.0.0-Paper.jar
```

### Step 6: Create Systemd Services
```bash
# Copy service files from this guide (or from backup if included)
sudo cp /opt/minecraft/services/*.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload
```

### Step 7: Create minecraft User (if needed)
```bash
# Check if user exists
id minecraft

# If not, create it
sudo useradd -r -s /bin/bash minecraft

# Fix permissions
sudo chown -R minecraft:minecraft /opt/minecraft/server-2
sudo chown -R minecraft:minecraft /opt/minecraft/backups
sudo chown -R minecraft:minecraft /opt/minecraft/afk-bot
sudo chown -R minecraft:minecraft /opt/minecraft/afk-bot2
```

### Step 8: Start Services
```bash
# Enable all services
sudo systemctl enable minecraft.service
sudo systemctl enable mc-tgbridge.service
sudo systemctl enable mc-web.service
sudo systemctl enable afk-bot.service
sudo systemctl enable afk-bot2.service
sudo systemctl enable minecraft-api.service

# Start minecraft (Telegram bot waits for it)
sudo systemctl start minecraft.service
sleep 5

# Check it's running
sudo systemctl status minecraft.service

# Wait 30-60s for world generation, then start others
sleep 30
sudo systemctl start mc-tgbridge.service
sudo systemctl start mc-web.service
sudo systemctl start minecraft-api.service

# AFKBots start after minecraft (see dependencies)
sudo systemctl start afk-bot.service
sleep 5
sudo systemctl start afk-bot2.service
```

### Step 9: Setup Cron Backup
```bash
# Create cron job
echo '0 3 * * * root /opt/minecraft/backup.sh >> /var/log/minecraft-backup.log 2>&1' | \
  sudo tee /etc/cron.d/minecraft-backup

# Test it
sudo /opt/minecraft/backup.sh
```

### Step 10: Setup Nginx Proxy (if web portal needed)
```bash
# Create nginx config
sudo nano /etc/nginx/sites-available/minecraft

# Content:
server {
    listen 80;
    server_name your-domain.uz;
    
    location / {
        proxy_pass http://localhost:8090;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/minecraft /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🔍 VERIFICATION CHECKLIST

After clone completes:

```bash
# 1. Check all services running
sudo systemctl status minecraft.service
sudo systemctl status mc-tgbridge.service
sudo systemctl status mc-web.service
sudo systemctl status afk-bot.service
sudo systemctl status afk-bot2.service
sudo systemctl status minecraft-api.service

# 2. Check Minecraft server logs
tail -f /opt/minecraft/server-2/logs/latest.log

# 3. Check Telegram bot is connected
grep -i "connected\|listening" /opt/minecraft/tg_bridge.py

# 4. Check web server
curl http://localhost:8090

# 5. Check AFKBots logged in
tail -f /opt/minecraft/afk-bot/afk-bot.log
tail -f /opt/minecraft/afk-bot2/afk-bot2.log

# 6. Check backups working
ls -lh /opt/minecraft/backups/

# 7. Connect to server
# Use Minecraft client to connect to new server
# Should see AFKBot and AFKBot2 in players list
```

---

## ⚠️ IMPORTANT NOTES

1. **Node.js Binary**: `/opt/minecraft/node/bin/node` is copied. Verify it runs on new server architecture (same OS/arch)
2. **Offline Mode**: Both AFKBots use offline auth. Bots connect with generated UUIDs (not user accounts)
3. **Permissions**: AFKBot/AFKBot2 have OP level 4 in ops.json. Keep these for `/tp` commands to work
4. **Backups**: rclone config MUST be same on new server, or update `BACKUP_REMOTE` in .env
5. **Telegram Bot**: Token in .env is live. Keep same token or Telegram won't recognize commands
6. **RCON Password**: Must match in server.properties and .env
7. **Web Portal**: Hosted on port 8090. Nginx should proxy it from port 80

---

## 📋 CURRENT SERVER CONFIG SUMMARY

| Component | Status | Port |
|-----------|--------|------|
| Minecraft Server | ✓ Running | 25565 |
| RCON | ✓ Enabled | 25575 |
| Telegram Bot | ✓ Running | - |
| Web Portal | ✓ Running | 8090 |
| AFKBot | ✓ Running | - |
| AFKBot2 | ✓ Running | - |
| API Server | ✓ Running | - |

**Players**: Sodiq, kingsman, Elbek, nusratov, AFKBot, AFKBot2
**Whitelist**: Enabled
**AuthMe**: Installed (v6.0.0)
**World Size**: 1.6GB

---

Generated: $(date)
