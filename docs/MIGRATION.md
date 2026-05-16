# 🔄 Migration & Replication Guide

**Qanday qilib ikkinchi server'da exact same setup qilinadi?**

---

## 📋 Jami Steps (Estimated Time: 30 minutes)

### **Phase 1: Preparation (5 min)**

#### Joriy server'dan backup oling:
```bash
# Current .env copy (sekret values bilan!)
scp /opt/minecraft/.env user@newserver:/tmp/.env.backup

# AuthMe database (agar xohsangiz)
scp -r /opt/minecraft/server-2/plugins/AuthMe/playerdata/* \
    user@newserver:/tmp/authme-backup/

# World backup (optional)
tar -czf /tmp/world-backup.tar.gz /opt/minecraft/server-2/world
scp /tmp/world-backup.tar.gz user@newserver:/tmp/
```

#### GitHub'da repository o'zingizga fork qiling:
```bash
# GitHub UI'da fork qiling yoki:
git clone https://github.com/YOU/minecraft-telegram-bot.git
```

---

### **Phase 2: New Server Setup (10 min)**

#### SSH qiling yangi server'ga:
```bash
ssh user@newserver
sudo su
```

#### Clone repository:
```bash
cd /opt/minecraft 2>/dev/null || mkdir -p /opt/minecraft
cd /opt/minecraft
git clone https://github.com/YOU/minecraft-telegram-bot.git .
chmod +x setup.sh backup.sh
```

#### Run setup script:
```bash
./setup.sh
```

**Setup script asks for:**
- Telegram Bot Token
- Chat ID va Topic IDs
- RCON Password
- Google Drive setup (optional)

**Setup script does:**
- ✅ Install dependencies
- ✅ Download Paper 1.21.11
- ✅ Setup AuthMe plugin
- ✅ Create systemd services
- ✅ Start server va bot

---

### **Phase 3: Restore Data (10 min)**

#### Option A: Restore AuthMe players (agar kerak bo'lsa):
```bash
# Old server'dan copy qilgan playerdata
scp -r user@oldserver:/opt/minecraft/server-2/plugins/AuthMe/playerdata/* \
    /opt/minecraft/server-2/plugins/AuthMe/playerdata/

# Server restart
systemctl restart minecraft.service
```

#### Option B: Restore world (agar kerak bo'lsa):
```bash
# World backup restore
cd /opt/minecraft/server-2

# Backup qiling current world'ni
mv world world-new
mkdir world

# Old world'ni restore
tar -xzf /tmp/world-backup.tar.gz --strip-components=4 -C world/

# Server restart
systemctl restart minecraft.service
```

---

### **Phase 4: Verification (5 min)**

#### Services working?
```bash
systemctl status minecraft.service
systemctl status mc-tgbridge.service

# Both ko'rsatsa "active" ✅
```

#### Server logs normal?
```bash
tail -50 /opt/minecraft/server-2/logs/latest.log

# Ko'rsa "Done!" yoki similar ✅
```

#### Telegram bot working?
```bash
# In Telegram, bot chat'da:
/status

# Javob bersa ✅
```

#### RCON working?
```bash
# Telegram'da:
/online

# Player count ko'rsatsa ✅
```

---

## 🔐 Security Checklist

```bash
# 1. .env file permissions
chmod 600 /opt/minecraft/.env
chmod 600 /opt/minecraft/.env.example

# 2. Backup permissions
chmod 700 /opt/minecraft/backups

# 3. Server user ownership
chown -R minecraft:minecraft /opt/minecraft/server-2
chown -R minecraft:minecraft /opt/minecraft/backups

# 4. SSH key setup (if needed)
ssh-copy-id user@newserver

# 5. Firewall rules
sudo ufw allow 22/tcp
sudo ufw allow 25565/tcp
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw enable
```

---

## 📊 Pre-Migration Checklist

Before closing old server:

- [ ] Final backup qildi
- [ ] All players notified
- [ ] Google Drive backup complete
- [ ] .env file copied
- [ ] AuthMe database backed up (agar players transfer qilinsa)
- [ ] World backup qildi (agar needed bo'lsa)
- [ ] DNS/IP updated (if external IP o'zgargan bo'lsa)

---

## 🚀 Post-Migration Tasks

On new server:

```bash
# 1. Update cron backup job
cat > /etc/cron.d/minecraft-backup <<EOF
0 3 * * * root /opt/minecraft/backup.sh >> /var/log/minecraft-backup.log 2>&1
EOF

# 2. Setup log rotation
cat > /etc/logrotate.d/minecraft <<EOF
/opt/minecraft/server-2/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 minecraft minecraft
}
EOF

# 3. Enable auto-start on reboot
systemctl enable minecraft.service mc-tgbridge.service

# 4. Test restart
systemctl reboot
# Wait 2 min, then:
systemctl status minecraft.service
systemctl status mc-tgbridge.service
```

---

## 🔄 Data Transfer Methods

### **Method 1: Git (Recommended)**
```bash
# Old server
cd /opt/minecraft
git add .
git commit -m "Pre-migration backup $(date)"
git push

# New server
git clone https://github.com/YOU/minecraft-telegram-bot.git /opt/minecraft
```

### **Method 2: rsync (Fast)**
```bash
# Old server'dan:
rsync -avz /opt/minecraft/ user@newserver:/opt/minecraft/

# Or new server'dan:
rsync -avz user@oldserver:/opt/minecraft/ /opt/minecraft/
```

### **Method 3: tar+scp (Universal)**
```bash
# Old server
tar -czf /tmp/minecraft.tar.gz /opt/minecraft/
scp /tmp/minecraft.tar.gz user@newserver:/tmp/

# New server
tar -xzf /tmp/minecraft.tar.gz -C /
```

---

## ⚠️ Common Migration Issues

### **Issue 1: RCON password mismatch**
```bash
# Check in .env
grep RCON_PASSWORD /opt/minecraft/.env

# Check in server.properties
grep rcon.password /opt/minecraft/server-2/server.properties

# Should match! If not:
systemctl stop minecraft.service
# Update .env or server.properties
systemctl start minecraft.service
```

### **Issue 2: Telegram bot not connecting**
```bash
# Check .env
cat /opt/minecraft/.env | grep TG_

# Restart bot
systemctl restart mc-tgbridge.service

# Check logs
journalctl -u mc-tgbridge.service -n 20
```

### **Issue 3: World doesn't load**
```bash
# Check permissions
ls -la /opt/minecraft/server-2/world/

# Should be: minecraft:minecraft

chown -R minecraft:minecraft /opt/minecraft/server-2/world/

# Restart
systemctl restart minecraft.service
```

### **Issue 4: Low disk space**
```bash
# Check
df -h /opt/minecraft

# Cleanup old backups
find /opt/minecraft/backups -name "*.zip" -mtime +30 -delete

# Or increase disk
# (Virtual machine'da - resize disk, then expand partition)
```

---

## 🔐 Secure Migration Steps

```bash
# 1. Generate new RCON password
openssl rand -base64 20

# 2. Update both .env va server.properties bilan new password
# 3. Test RCON connection
# 4. Backup all configs
# 5. Update DNS (agar external IP changed bo'lsa)
# 6. Test everything works
# 7. Notify players
# 8. Graceful shutdown on old server
# 9. Keep old server backup minimum 7 days
```

---

## 📈 Scaling to Multiple Servers

Agar 2+ servers kerak bo'lsa:

```bash
# Server 1: server-a.example.com
# Server 2: server-b.example.com

# Each has own:
# - .env (different TG_TOKEN yoki CHAT_ID)
# - server-2/ directory
# - Systemd services

# Central management (optional):
# - rclone sync uchun shared backup storage
# - Centralized Telegram group
# - Load balancer (nginx/haproxy)
```

---

## 🛡️ Backup Strategy

**Daily rotation:**
```
Day 1: minecraft-2026-05-16.zip (local + Google Drive)
Day 2: minecraft-2026-05-17.zip (local + Google Drive)
...
Day 7: minecraft-2026-05-22.zip (Google Drive only)
Day 8: minecraft-2026-05-23.zip (deleted after 7 days)
```

**Manual backup qilish:**
```bash
/opt/minecraft/backup.sh

# Verify backup created
ls -lh /opt/minecraft/backups/ | tail -1

# Verify uploaded to Google Drive
rclone ls gdrive:minecraft-backups/ | tail -3
```

---

## 📞 Rollback Plan

Agar new server'da problem bo'lsa:

```bash
# Old server'ga qaytarish
ssh user@oldserver

systemctl start minecraft.service
systemctl start mc-tgbridge.service

# Update DNS back to old server IP
# Notify players

# Then debug new server separately
```

---

## ✅ Final Checklist

- [ ] Git repository committed va pushed
- [ ] All backups downloaded
- [ ] New server setup script ran successfully
- [ ] Services active va working
- [ ] Telegram bot responding
- [ ] Server accessible on 25565
- [ ] World loaded correctly
- [ ] Backups functioning
- [ ] Cron job scheduled
- [ ] Firewall configured
- [ ] SSH access verified
- [ ] DNS updated (agar needed)
- [ ] Players notified
- [ ] Old server gracefully shut down (optional)

---

**Ready for migration! 🚀**
