# 🎮 Server Clone - Quick Commands

## 1️⃣ BACKUP & COMPRESS (Current Server)

```bash
# Create complete backup
cd /opt/minecraft
tar czf minecraft-clone-$(date +%Y%m%d-%H%M%S).tar.gz \
  --exclude='./backups/*.zip' \
  --exclude='./server-2/logs/*' \
  --exclude='./afk-bot/afk-bot.log' \
  --exclude='./afk-bot2/afk-bot2.log' \
  .

# Size check
ls -lh minecraft-clone-*.tar.gz

# Upload to Google Drive (if using rclone)
rclone copy minecraft-clone-*.tar.gz gdrive:minecraft-clone/
```

## 2️⃣ TRANSFER TO NEW SERVER

```bash
# From current server
scp minecraft-clone-*.tar.gz user@newserver:/tmp/

# Or via rsync
rsync -avz minecraft-clone-*.tar.gz newserver:/tmp/
```

## 3️⃣ SETUP NEW SERVER

```bash
# SSH to new server
ssh user@newserver

# Create directory
sudo mkdir -p /opt/minecraft
cd /opt/minecraft

# Extract backup
sudo tar xzf /tmp/minecraft-clone-*.tar.gz

# Fix permissions
sudo chown -R minecraft:minecraft /opt/minecraft
sudo chmod -R 755 /opt/minecraft
```

## 4️⃣ INSTALL DEPENDENCIES (New Server)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Java & tools
sudo apt install -y openjdk-21-jre-headless python3 python3-pip python3-dotenv rclone git

# Install Python libs
pip3 install mcrcon python-telegram-bot --break-system-packages
```

## 5️⃣ SETUP SYSTEMD SERVICES

```bash
# Create minecraft user (if not exists)
sudo useradd -r -s /bin/bash minecraft 2>/dev/null || true

# Reload systemd
sudo systemctl daemon-reload

# Enable all services
sudo systemctl enable minecraft.service
sudo systemctl enable mc-tgbridge.service
sudo systemctl enable mc-web.service
sudo systemctl enable afk-bot.service
sudo systemctl enable afk-bot2.service
sudo systemctl enable minecraft-api.service
```

## 6️⃣ START SERVICES IN ORDER

```bash
# Start Minecraft server first
sudo systemctl start minecraft.service

# Wait for world load
sleep 30

# Start bridge & web
sudo systemctl start mc-tgbridge.service
sudo systemctl start mc-web.service
sudo systemctl start minecraft-api.service

# Start AFK bots (depend on minecraft)
sudo systemctl start afk-bot.service
sleep 3
sudo systemctl start afk-bot2.service

# Check status
sudo systemctl status minecraft.service
sudo systemctl status afk-bot.service
sudo systemctl status afk-bot2.service
```

## 7️⃣ VERIFY SETUP

```bash
# Check Minecraft logs
tail -f /opt/minecraft/server-2/logs/latest.log

# Check Telegram bot is connected
sudo systemctl status mc-tgbridge.service
tail -f /var/log/syslog | grep -i telegram

# Check AFKBots
tail -f /opt/minecraft/afk-bot/afk-bot.log
tail -f /opt/minecraft/afk-bot2/afk-bot2.log

# Check web portal
curl http://localhost:8090

# Check API
curl http://localhost:8089/status 2>/dev/null || echo "API pending..."
```

## 8️⃣ SETUP BACKUPS

```bash
# Create cron job
echo '0 3 * * * root /opt/minecraft/backup.sh >> /var/log/minecraft-backup.log 2>&1' | \
  sudo tee /etc/cron.d/minecraft-backup

# Test backup immediately
sudo /opt/minecraft/backup.sh

# Check it worked
ls -lh /opt/minecraft/backups/
```

## 9️⃣ SETUP NGINX PROXY (Optional)

```bash
# Create nginx config
cat << 'EOF' | sudo tee /etc/nginx/sites-available/minecraft-portal
server {
    listen 80;
    server_name mc.sodops.uz;
    
    location / {
        proxy_pass http://localhost:8090;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/minecraft-portal /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🔟 TROUBLESHOOTING

```bash
# Minecraft won't start?
sudo systemctl start minecraft.service
journalctl -u minecraft.service -n 50 -f

# Check Java heap
ps aux | grep java

# AFKBot connection issues?
grep -i "error\|connected\|login" /opt/minecraft/afk-bot/afk-bot.log

# Telegram bot not responding?
grep -i "webhook\|error" /var/log/syslog | tail -20

# Port already in use?
lsof -i :25565    # Minecraft
lsof -i :25575    # RCON
lsof -i :8090     # Web portal
```

## 📋 QUICK COMMANDS

```bash
# Restart all services
sudo systemctl restart minecraft.service
sleep 30
sudo systemctl restart mc-tgbridge.service
sudo systemctl restart mc-web.service
sudo systemctl restart afk-bot.service
sudo systemctl restart afk-bot2.service

# Check all running
sudo systemctl status minecraft* afk-bot*

# View all logs
journalctl -u minecraft.service -n 100
journalctl -u mc-tgbridge.service -n 100
journalctl -u afk-bot.service -n 100

# Stop everything
sudo systemctl stop minecraft.service afk-bot.service afk-bot2.service mc-tgbridge.service

# Manual backup
/opt/minecraft/backup.sh

# Check disk usage
du -sh /opt/minecraft/*
du -sh /opt/minecraft/backups/
```

## ⚠️ IMPORTANT NOTES

1. **Node.js Binary**: Check it matches new server architecture
   ```bash
   /opt/minecraft/node/bin/node --version
   ```

2. **Minecraft User**: Must own server files
   ```bash
   sudo chown -R minecraft:minecraft /opt/minecraft/server-2
   sudo chown -R minecraft:minecraft /opt/minecraft/backups
   ```

3. **Telegram Token**: Keep same .env unless changing bot
   ```bash
   cat /opt/minecraft/.env | grep TG_
   ```

4. **RCON Password**: Must match server.properties
   ```bash
   grep rcon.password /opt/minecraft/server-2/server.properties
   ```

5. **Whitelist Players**: Already in whitelist.json
   ```bash
   cat /opt/minecraft/server-2/whitelist.json
   ```

6. **Player UUIDs**: Use offline-mode format
   ```bash
   uuid3('00000000-0000-0000-0000-000000000000', 'OfflineMode:PlayerName')
   ```

---

Generated: 2026-06-10
All files location: `/opt/minecraft/`
