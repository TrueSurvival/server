# 🎮 Minecraft Server + Telegram Bot Setup Guide

**Version:** 1.0 | **Date:** May 16, 2026

Ushbu repository Minecraft Paper server'ni Telegram bot bilan connect qilgan complete setup va automation scriptlarini o'z ichiga oladi.

---

## 📋 **Nima Bu?**

- ✅ **Paper 1.21.11** Minecraft Server (Fabric free version)
- ✅ **AuthMe Plugin** - Secure player authentication with GUI login
- ✅ **Telegram Bot** - Server management + chat bridge
- ✅ **Automated Backups** - Daily backups to Google Drive
- ✅ **Systemd Services** - Auto-restart + persistent running
- ✅ **Easy Configuration** - Single `.env` file setup

---

## 🚀 **Quick Start (5 minutes)**

### **1️⃣ Prerequisites**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y openjdk-21-jre-headless git python3 python3-pip rclone zip

# Yuklash
pip3 install mcrcon python-telegram-bot
```

### **2️⃣ Folder Setup**
```bash
mkdir -p /opt/minecraft
cd /opt/minecraft
git clone <this-repo> .
chmod +x backup.sh
```

### **3️⃣ Configuration (.env)**
```bash
# Example copy qiling
cp .env.example .env

# Text editor'da o'zgartiring
nano .env
```

**Zarur sozlamalar:**
```env
# Telegram Bot
TG_TOKEN=your_bot_token_here          # BotFather'dan oling
TG_CHAT_ID=-1001234567890             # Chat ID
CHAT_TOPIC_ID=6                       # Forum topic ID
LOG_TOPIC_ID=9555                     # Log topic ID
ADMIN_IDS=123456789                   # Your user ID

# Minecraft RCON
RCON_PASSWORD=super_secret_password   # server.properties'dan oling
RCON_HOST=localhost
RCON_PORT=25575

# Backup
BACKUP_REMOTE=gdrive:minecraft-backups/  # rclone path
BACKUP_RETENTION_DAYS=7               # Necha kundan keyin o'chirish
```

### **4️⃣ Server Sozlash**
```bash
# Paper server'ni download qiling
cd /opt/minecraft/server-2
# paper-1.21.11-131.jar o'rnatish kerak

# Plugins sozlash
mkdir -p plugins
cd plugins
# AuthMe plugin'ni download qiling
wget https://github.com/AuthMe/AuthMeReloaded/releases/download/5.6.0-beta/AuthMe-6.0.0-Paper.jar
```

### **5️⃣ Systemd Services**
```bash
sudo tee /etc/systemd/system/minecraft.service > /dev/null <<EOF
[Unit]
Description=Minecraft Paper Server
After=network.target

[Service]
User=minecraft
WorkingDirectory=/opt/minecraft/server-2
ExecStart=/usr/bin/java -Xms512M -Xmx2G -jar paper-1.21.11-131.jar nogui
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/mc-tgbridge.service > /dev/null <<EOF
[Unit]
Description=Minecraft Telegram Bridge
After=minecraft.service

[Service]
User=root
WorkingDirectory=/opt/minecraft
EnvironmentFile=/opt/minecraft/.env
ExecStart=/usr/bin/python3 /opt/minecraft/tg_bridge.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable minecraft.service mc-tgbridge.service
sudo systemctl start minecraft.service mc-tgbridge.service
```

---

## 📁 **Fayl Tuzilishi**

```
/opt/minecraft/
├── README.md                    # Bu fayl
├── SETUP.md                     # Batafsil setup guide
├── backup.sh                    # Backup script
├── tg_bridge.py                 # Telegram bot
├── .env                         # Configuration (MODE 600)
├── .env.example                 # Template
├── server-2/                    # Paper server directory
│   ├── server.properties        # Server config
│   ├── eula.txt                 # EULA confirm
│   ├── plugins/
│   │   └── AuthMe-6.0.0-Paper.jar
│   └── logs/
├── backups/                     # Local backups
│   └── minecraft-2026-05-16_03-11-56.zip
└── systemd-notes.md             # Internal notes
```

---

## ⚙️ **Environment Variables (.env)**

### **Telegram Bot Sozlash**

```env
# 1. BotFather'da bot yarating (@BotFather)
TG_TOKEN=7236829228:AAH5190wnRjsBOa6YKaoIO6glLfgBi2gh5A

# 2. Telegram group'ni forum'ga aylantiring
# 3. Group ID'ni oling (@userinfobot yordamida)
TG_CHAT_ID=-1001914112188

# 4. Forum topics yarating va ID'larni oling
CHAT_TOPIC_ID=6           # Players' chat topic
LOG_TOPIC_ID=9555         # Server logs topic
CHAT_TOPIC_ID=2180        # News topic (optional)

# 5. Sizning Telegram user ID'ingiz
ADMIN_IDS=6984554888
```

### **Minecraft Server Sozlash**

```env
# server.properties'dan RCON sozlamalarini oling
RCON_HOST=localhost
RCON_PORT=25575
RCON_PASSWORD=your_rcon_password

# Server'ni qaysi papkada ishlatish
LOG_FILE=/opt/minecraft/server-2/logs/latest.log
MINECRAFT_SERVICE=minecraft
```

### **Backup Sozlash**

```env
# Google Drive backup uchun
# rclone config qiling: rclone config
BACKUP_REMOTE=gdrive:minecraft-backups/
BACKUP_DIR=/opt/minecraft/backups
BACKUP_RETENTION_DAYS=7        # 7 kundan keyin auto-delete

# Backup script'i qayerda
BACKUP_SCRIPT=/opt/minecraft/backup.sh
```

---

## 🔧 **Asosiy Komandalar**

### **Telegram Bot Commands**

**Umumiy (Hamm):**
- `/start` - Bot info
- `/help` - Commands list
- `/online` - Online players
- `/tps` - Server performance
- `/status` - Quick server status
- `/ping` - RCON check

**Admin Commands:**
- `/server start|stop|restart|status` - Service control
- `/backup` - Manual backup
- `/health` - Disk/TPS/backup status
- `/logs [n]` - Last n log lines
- `/mc <command>` - Direct RCON command
- `/op <nick>` - Give OP
- `/kick <nick> [reason]` - Kick player
- `/ban <nick> [reason]` - Ban player

### **Backup Script**

```bash
# Manual backup qilish
./backup.sh

# Cron'da avtomatik (har kuni 3:00 AM)
0 3 * * * /opt/minecraft/backup.sh >> /var/log/minecraft-backup.log 2>&1
```

---

## 🔐 **Security Best Practices**

### **1. .env File Permission**
```bash
chmod 600 /opt/minecraft/.env    # Faqat owner o'qiy oladi
chmod 600 /opt/minecraft/.env.example  # Shared template uchun (secrets without real values)
```

### **2. Secrets Storage**
```bash
# ❌ Secrets'ni code'da hard-code qilmang
# ✅ Har doim .env'dan oling

# Misal:
# RCON_PASSWORD=$(grep RCON_PASSWORD .env | cut -d= -f2)
```

### **3. Backup Encryption**
```bash
# rclone'ni encryption bilan sozlang (optional)
rclone config --edit
# B2 yoki Google Drive'da encrypted remote setup qiling
```

### **4. Firewall**
```bash
# RCON port'ni tashqi'dan block qiling
sudo ufw allow 25565/tcp    # Minecraft protocol
sudo ufw deny 25575/tcp     # RCON (localhost only)
```

---

## 🐛 **Troubleshooting**

### **Bot ishlamayotgan**
```bash
# Logs tekshiring
systemctl status mc-tgbridge.service
journalctl -u mc-tgbridge.service -n 50

# .env sozlamalarini tekshiring
cat /opt/minecraft/.env | grep TG_TOKEN
```

### **Backup ishlami**
```bash
# Test qilish
/opt/minecraft/backup.sh

# rclone sozlash
rclone config
rclone listremotes

# Backup logs
tail -f /var/log/minecraft-backup.log
```

### **AuthMe login ishlami**
```bash
# Server logs tekshiring
tail -f /opt/minecraft/server-2/logs/latest.log | grep -i auth

# Plugin reload
/execute
/plugman reload AuthMe
```

---

## 📊 **Monitoring**

### **Service Status**
```bash
systemctl status minecraft.service
systemctl status mc-tgbridge.service

# Auto-restart logs
journalctl -u minecraft.service -n 20
```

### **Resource Usage**
```bash
ps aux | grep java
ps aux | grep python3

# Real-time monitoring
top -p $(pgrep -f "java.*paper")
```

---

## 🔄 **Boshqa Server'ga Migration**

Boshqa serverni o'rnatish uchun:

```bash
# 1. New server'da repo clone qiling
git clone <this-repo> /opt/minecraft

# 2. .env copy qiling va edit qiling
cp .env.example .env
nano .env  # O'zgarishlari qilish

# 3. Backup'larni restore qilish
cd /opt/minecraft/backups
unzip minecraft-2026-05-16_03-11-56.zip

# 4. Services'ni setup qiling
sudo systemctl enable minecraft.service mc-tgbridge.service
sudo systemctl start minecraft.service mc-tgbridge.service
```

---

## 📞 **Support**

- **Paper Docs:** https://docs.papermc.io
- **AuthMe GitHub:** https://github.com/AuthMe/AuthMeReloaded
- **python-telegram-bot:** https://python-telegram-bot.readthedocs.io
- **rclone:** https://rclone.org

---

## 📝 **Version History**

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-05-16 | Initial setup |

---

## ✅ **Setup Checklist**

- [ ] Java 21+ o'rnatilgan
- [ ] Paper server downloaded
- [ ] AuthMe plugin installed
- [ ] `.env` file created va sozlangan
- [ ] Telegram bot token olingan
- [ ] RCON password server.properties'da sozlangan
- [ ] rclone Google Drive'ga connect qilgan
- [ ] Systemd services created va enabled
- [ ] Backup script tested
- [ ] Telegram bot commands working
- [ ] Cron backup scheduled
- [ ] Firewall configured

---

**Happy Gaming! 🎮**
