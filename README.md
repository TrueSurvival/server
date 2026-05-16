# 🎮 Minecraft Paper + Telegram Bot

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Paper 1.21.11](https://img.shields.io/badge/Paper-1.21.11-brightgreen)](https://papermc.io/)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-blue?logo=telegram)](https://telegram.org/)

Complete, production-ready Minecraft server with **Telegram bot integration**, **automated backups**, and **secure player authentication**.

**⚡ Key Features:**
- 🎮 Paper 1.21.11 Minecraft server
- 🔐 AuthMe authentication with GUI login
- 💬 Bidirectional Telegram chat bridge
- 📦 Automated daily backups to Google Drive
- 🤖 Server management via Telegram commands
- 🔧 One-click setup with `setup.sh`
- 📚 Comprehensive documentation & guides

---

## 🚀 Quick Start

### **Option 1: Automated Setup (Recommended)**
```bash
sudo su
mkdir -p /opt/minecraft && cd /opt/minecraft
git clone https://github.com/YOUR_REPO/minecraft-telegram-bot.git .
chmod +x scripts/setup.sh
./scripts/setup.sh
```

**Setup script will:**
- Install Java, Python, dependencies
- Download Paper 1.21.11
- Setup AuthMe plugin
- Configure Telegram bot
- Create systemd services
- Start server automatically

⏱️ **Time:** ~2-3 minutes | 📝 **Prompts:** 5 interactive questions

### **Option 2: Fully Automatic (CI/CD Ready)**
```bash
export TG_TOKEN="your_token" TG_CHAT_ID="-1001234567890" \
       ADMIN_IDS="123456789" RCON_PASSWORD="password" AUTO_RCLONE="skip"

sudo -E bash scripts/setup.sh
```

**Zero user interaction - perfect for:**
- Docker containers
- Kubernetes deployments
- GitHub Actions CI/CD
- Infrastructure-as-Code

See [AUTOMATIC_SETUP.md](AUTOMATIC_SETUP.md) for full details.

### **Option 3: Manual Setup**
See [📘 docs/QUICK_START.md](docs/QUICK_START.md) for step-by-step instructions.

---

## 📋 Requirements

- **OS:** Ubuntu 20.04+ or Debian 11+
- **CPU:** 2+ cores
- **RAM:** 2GB+ (4GB recommended)
- **Disk:** 5GB+ (for backups)
- **Java:** OpenJDK 21+
- **Telegram:** Bot token (from [@BotFather](https://t.me/botfather))
- **Google Account:** (for backup storage)

---

## 🎮 Features

### **Paper Minecraft Server**
- Latest Paper 1.21.11 build
- Optimized Java flags (G1GC)
- Performance plugins (optional)
- Full vanilla compatibility

### **AuthMe Authentication**
- Secure password-based login
- Beautiful GUI dialog (Minecraft 1.21.11+)
- Email recovery system
- Player data protection
- SQLite database

### **Telegram Bot Commands**

| Command | Permission | Description |
|---------|-----------|-------------|
| `/online` | Public | Show online players |
| `/status` | Public | Server status & TPS |
| `/tps` | Public | TPS & MSPT metrics |
| `/health` | Admin | Disk, memory, backup status |
| `/server <start\|stop\|restart>` | Admin | Control server |
| `/backup` | Admin | Manual backup |
| `/logs [n]` | Admin | Last n log lines |
| `/mc <command>` | Admin | Direct RCON command |
| `/kick <nick>` | Admin | Kick player |
| `/ban <nick>` | Admin | Ban player |
| `/op <nick>` | Admin | Give OP |

### **Chat Bridge**
- ✅ Minecraft chat → Telegram
- ✅ Telegram messages → Minecraft  
- ✅ Smart coordinate detection
- ✅ Filtered logs in separate topic
- ✅ Per-player message formatting

### **Automated Backups**
- ⏰ Daily at 3:00 AM (configurable)
- 📦 Full world + config backup
- ☁️ Upload to Google Drive
- 🗑️ Auto-delete old backups (7+ days)
- 📊 Backup status in Telegram

### **Auto-Restart & Monitoring**
- 🔄 systemd service auto-restart on crash
- 📝 Persistent logging
- 🔔 Telegram notifications
- 🛡️ Graceful shutdown handling

---

## 📁 Project Structure

```
.
├── README.md                      # This file
├── LICENSE                        # MIT License
├── CONTRIBUTING.md                # Contribution guidelines
├── ARCHITECTURE.md                # System design
├── .gitignore                    # Git exclusions
│
├── docs/                         # Documentation
│   ├── QUICK_START.md           # 10-minute setup
│   ├── README.md                # Full reference
│   ├── TROUBLESHOOTING.md       # Common issues
│   └── MIGRATION.md             # Deploy to new server
│
├── scripts/                      # Executable scripts
│   ├── setup.sh                 # One-click installer
│   └── backup.sh                # Backup automation
│
├── templates/                    # Configuration templates
│   └── .env.example             # Environment template
│
└── src/                         # Source code
    └── tg_bridge.py             # Main Telegram bot
```

### 🚫 Not in Git (Security)
```
/opt/minecraft/
├── .env                  # Secrets (RCON password, bot token)
├── server-2/             # Active server (running)
└── backups/              # Backup archives
```

---

## ⚙️ Configuration

All configuration via single `.env` file:

```env
# Telegram
TG_TOKEN=your_bot_token_here
TG_CHAT_ID=-1001234567890
CHAT_TOPIC_ID=6
LOG_TOPIC_ID=9555
ADMIN_IDS=123456789

# Minecraft RCON
RCON_HOST=localhost
RCON_PORT=25575
RCON_PASSWORD=secure_password

# Server
LOG_FILE=/opt/minecraft/server-2/logs/latest.log
MINECRAFT_SERVICE=minecraft

# Backup
BACKUP_SCRIPT=/opt/minecraft/scripts/backup.sh
BACKUP_DIR=/opt/minecraft/backups
BACKUP_REMOTE=gdrive:minecraft-backups/
BACKUP_RETENTION_DAYS=7
```

See [📘 docs/README.md](docs/README.md) for complete configuration reference.

---

## 🚨 Troubleshooting

### Bot not responding?
```bash
systemctl status mc-tgbridge.service
journalctl -u mc-tgbridge.service -n 20
```

### Server won't start?
```bash
tail -50 /opt/minecraft/server-2/logs/latest.log
systemctl status minecraft.service
```

### Backup failing?
```bash
/opt/minecraft/scripts/backup.sh
tail -20 /var/log/minecraft-backup.log
```

**Full troubleshooting guide:** [🔧 docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [📘 docs/QUICK_START.md](docs/QUICK_START.md) | 10-minute setup guide |
| [📖 docs/README.md](docs/README.md) | Complete reference |
| [🔧 docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Problem solving |
| [🏗️ ARCHITECTURE.md](ARCHITECTURE.md) | System design & flow |
| [🔄 docs/MIGRATION.md](docs/MIGRATION.md) | New server deployment |
| [🤝 CONTRIBUTING.md](CONTRIBUTING.md) | Development guide |

---

## 🔐 Security

✅ **Security Features:**
- Secrets in `.env` (gitignored, chmod 600)
- RCON localhost-only (not exposed)
- Telegram admin verification
- No credentials in logs
- Password encryption (SHA256/BCrypt)
- Guild ID verification in bot

⚠️ **Best Practices:**
- Keep `.env` file secure
- Use strong RCON password
- Restrict admin IDs to trusted users
- Regularly backup to external storage
- Use firewall to limit port access

---

## 🛠️ Advanced Setup

### Multiple Servers
Deploy identical setup to multiple machines:
```bash
# Server 1
git clone ... /opt/minecraft
./scripts/setup.sh

# Server 2
git clone ... /opt/minecraft
./scripts/setup.sh
# (Use different RCON_PASSWORD, TG_CHAT_ID per server)
```

### Docker (Coming Soon)
```bash
docker build -t minecraft-bot .
docker run -d --name minecraft -p 25565:25565 \
  -v /opt/minecraft/.env:/.env \
  minecraft-bot
```

### Performance Tuning
- Adjust `-Xmx4G` in systemd service for more RAM
- Tune Bukkit server.properties
- Use performance plugins (Lithium, Sodium)

See [🏗️ ARCHITECTURE.md](ARCHITECTURE.md#performance-considerations)

---

## 📊 System Architecture

```
Minecraft Server ◄──RCON──► Telegram Bot
       │                          │
       ▼                          ▼
   AuthMe Plugin          Chat Bridge
    (GUI Login)           (Message relay)
       │                          │
       └──────────┬───────────────┘
                  │
           ┌──────▼───────┐
           │ Backup System│
           │(Daily 3:00AM)│
           └──────┬───────┘
                  │
            Google Drive
           (Cloud Storage)
```

Full architecture details: [🏗️ ARCHITECTURE.md](ARCHITECTURE.md)

---

## 🤝 Contributing

We welcome contributions! See [🤝 CONTRIBUTING.md](CONTRIBUTING.md) for:
- Bug reporting
- Feature requests  
- Code style guidelines
- PR process
- Development setup

### Ways to Contribute:
- 🐛 Report bugs
- ✨ Suggest features
- 📖 Improve documentation
- 💻 Submit code/fixes
- 🧪 Add tests
- 🌍 Translate

---

## 📈 Project Status

| Component | Status |
|-----------|--------|
| Minecraft Server | ✅ Production Ready |
| Telegram Bot | ✅ Production Ready |
| AuthMe Plugin | ✅ Production Ready |
| Backup System | ✅ Production Ready |
| Setup Script | ✅ Fully Automated |
| Documentation | ✅ Complete |
| Tests | 🔶 In Progress |
| Docker | 🔶 Planned |

---

## 📦 Dependencies

### Server
- **Paper 1.21.11** - Minecraft server
- **AuthMe** - Authentication plugin
- **OpenJDK 21** - Java runtime

### Bot
- **python-telegram-bot** - Telegram integration
- **mcrcon** - RCON client
- **rclone** - Cloud backup

### Infrastructure
- **systemd** - Service management
- **rclone** - Google Drive sync
- **cron** - Task scheduling

See `scripts/setup.sh` for full installation commands.

---

## 📄 License

This project is licensed under the **MIT License** - see [LICENSE](LICENSE) for details.

---

## 📞 Support

- 📖 **Documentation:** Check [docs/](docs/) folder
- 🐛 **Bug Reports:** [GitHub Issues](../../issues)
- 💡 **Feature Requests:** [GitHub Discussions](../../discussions)
- 💬 **Questions:** [GitHub Discussions](../../discussions)

---

## 🎉 Acknowledgments

Built with:
- [Paper MC](https://papermc.io/) - Minecraft server
- [AuthMe](https://github.com/AuthMe/AuthMeReloaded) - Authentication
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Bot framework
- [rclone](https://rclone.org/) - Cloud sync

---

## 🚀 Roadmap

### v1.0 (Current)
- ✅ Core server + bot
- ✅ AuthMe login
- ✅ Chat bridge
- ✅ Backup system
- ✅ Documentation

### v1.1 (Planned)
- 🔶 Player whitelist management via Telegram
- 🔶 Server stats dashboard
- 🔶 Multi-language support
- 🔶 Performance improvements

### v2.0 (Future)
- 🔲 Docker containerization
- 🔲 Web admin panel
- 🔲 Discord alternative
- 🔲 Multiple server dashboard

---

**Last Updated:** 2026-05-16  
**Maintained by:** The Community

⭐ If you find this useful, please give it a star! [⭐ Star us on GitHub](../../)
