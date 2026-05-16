# ⚡ Quick Start Guide (10 Minutes)

**For impatient people who just want it working!**

---

## 📋 Prerequisites

You need:
- Ubuntu/Debian server (or WSL)
- Root access (`sudo`)
- Telegram Bot (from @BotFather)
- Google Account (for backup storage)

---

## 🚀 Step-by-Step Setup

### **Step 1: Clone Repository**
```bash
sudo bash
mkdir -p /opt/minecraft
cd /opt/minecraft
git clone <repo> .  # Or download files manually
chmod +x setup.sh backup.sh
```

### **Step 2: Run Setup Script**
```bash
./setup.sh
```

**Script will ask for:**
1. **Telegram Bot Token** - Get from @BotFather (`/token`)
2. **Telegram Chat ID** - Get from @userinfobot in your group
3. **Topic IDs** - Forum topic IDs (can use default 6 and 9555)
4. **Admin ID** - Your Telegram user ID (use @userinfobot)
5. **RCON Password** - Any secure password (will be set in server.properties)

### **Step 3: Wait & Verify**
```bash
# Wait 30 seconds for server to start
sleep 30

# Check status
systemctl status minecraft.service
systemctl status mc-tgbridge.service

# See logs
tail -f /opt/minecraft/server-2/logs/latest.log
```

### **Step 4: Test in Telegram**
- Send `/status` to bot
- Should see online players (will be 0 if no one joined)
- If works → ✅ **Setup complete!**

### **Step 5: (Optional) Setup Google Drive Backups**
```bash
rclone config
# Select: N (new remote)
# Name: gdrive
# Choose: Google Drive
# Follow OAuth steps
```

---

## 🎮 First Time Playing

1. **Server IP:** `your_server_ip:25565`
2. **Join server**
3. **Login GUI appears** - Create password
4. **Enter password** - In GUI dialog (not chat!)
5. **Play!**

---

## 📱 Telegram Bot Commands

- `/online` - Who's playing
- `/status` - Server status
- `/help` - All commands
- `/backup` - Manual backup (admin only)
- `/server restart` - Restart (admin only)

---

## ⚠️ Common Mistakes

❌ **Don't:**
- Copy `.env` file to GitHub (contains secrets!)
- Use chat for passwords (type in login GUI!)
- Run setup without sudo
- Close terminal before "Setup complete!" message

✅ **Do:**
- Keep `.env` file safe (chmod 600)
- Verify all .env values before running setup
- Read error messages carefully
- Check logs if something doesn't work

---

## 🆘 If Something Breaks

```bash
# Check what's wrong
systemctl status minecraft.service
journalctl -u minecraft.service -n 20

# Restart
systemctl restart minecraft.service
systemctl restart mc-tgbridge.service

# Check logs
tail -f /opt/minecraft/server-2/logs/latest.log
```

**Still broken?** → See `TROUBLESHOOTING.md`

---

## 📁 Important Files

```
/opt/minecraft/
├── .env                    # YOUR SECRETS (chmod 600!)
├── backup.sh              # Backup script
├── tg_bridge.py           # Telegram bot
├── setup.sh               # Setup automation
├── README.md              # Full documentation
├── TROUBLESHOOTING.md     # Common issues
└── server-2/              # Server directory
    ├── server.properties  # Server config
    ├── plugins/
    │   └── AuthMe-6.0.0-Paper.jar
    └── logs/latest.log
```

---

## 🔄 Daily Operations

**Check server status:**
```bash
systemctl status minecraft.service
```

**View last 50 logs:**
```bash
tail -50 /opt/minecraft/server-2/logs/latest.log
```

**Restart server:**
```bash
systemctl restart minecraft.service
```

**Manual backup:**
```bash
/opt/minecraft/backup.sh
```

**Update .env:**
```bash
nano /opt/minecraft/.env
systemctl restart mc-tgbridge.service
```

---

## ✅ Verification Checklist

After setup, verify all working:

```bash
# 1. Services running?
systemctl is-active minecraft.service      # Should be: active
systemctl is-active mc-tgbridge.service    # Should be: active

# 2. Ports listening?
netstat -tuln | grep 25565                # Minecraft port
netstat -tuln | grep 25575                # RCON port

# 3. Files exist?
ls -l /opt/minecraft/{.env,backup.sh,tg_bridge.py,server-2/paper-*.jar}

# 4. Can connect to server?
timeout 3 bash -c 'echo > /dev/tcp/127.0.0.1/25565' && echo "✅ OK"

# 5. Bot can send messages?
# Send /ping to bot → Should respond "🏓 Pong"
```

All ✅? → **Setup successful!** 🎉

---

## 📞 Need Help?

1. **Check logs first:** `journalctl -u minecraft.service -n 50`
2. **Search TROUBLESHOOTING.md** for your error
3. **Check .env values** are correct
4. **Restart everything:** `systemctl restart minecraft.service mc-tgbridge.service`

---

**That's it! You're ready to go! 🚀**

*For advanced configuration, see README.md*
