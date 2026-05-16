# 🏗️ System Architecture

## Overview

```
┌─────────────────────────────────────────────────────────┐
│          Minecraft + Telegram Bot Integration           │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
   ┌─────────┐       ┌──────────┐      ┌─────────┐
   │ Minecraft│       │ AuthMe   │      │ Telegram│
   │  Paper   │       │ Plugin   │      │   Bot   │
   │ 1.21.11  │       │  (GUI)   │      │(Python) │
   └─────────┘       └──────────┘      └─────────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          │
                    ┌─────▼─────┐
                    │    RCON    │
                    │Connection  │
                    └─────┬─────┘
                          │
                    ┌─────▼─────┐
                    │  Logging   │
                    │  & Chat    │
                    │  Bridge    │
                    └─────┬─────┘
                          │
                ┌─────────┼─────────┐
                │         │         │
                ▼         ▼         ▼
            ┌───────┐ ┌────────┐ ┌──────┐
            │Google │ │System │ │Local│
            │ Drive │ │ Logs  │ │ .env│
            │Backup │ │       │ │Config│
            └───────┘ └────────┘ └──────┘
```

---

## Components

### 1. **Minecraft Paper Server** (server-2/)
```
server-2/
├── paper-1.21.11-131.jar    # Main server binary
├── server.properties         # Server configuration
├── eula.txt                  # EULA acceptance
├── plugins/
│   └── AuthMe-6.0.0-Paper.jar # Authentication plugin
├── world/                    # Game world data
├── logs/
│   └── latest.log           # Server logs (tailed by bot)
└── config/
    └── AuthMe/              # AuthMe configuration
```

**Java Process:**
```bash
java -Xms512M -Xmx2G [G1GC FLAGS] -jar paper-1.21.11-131.jar nogui
```

---

### 2. **AuthMe Plugin** (Authentication)
```
Minecraft Client
    │
    ▼
┌─────────────────────┐
│ Pre-join GUI Dialog │ (Paper feature)
│ 🔐 Server Login     │ (Customized messages)
└─────────────────────┘
    │
    ▼
├─ GUI Password Entry (encrypted)
├─ CAPS LOCK warning
├─ Recovery email option
└─ Registration for new players

Storage: SQLite (plugins/AuthMe/authme.db)
```

---

### 3. **Telegram Bot** (tg_bridge.py)

#### Bidirectional Communication:

```
        MINECRAFT ◄──────────► TELEGRAM
        
Minecraft Chat                Telegram Chat
    │                              │
    ▼                              ▼
┌──────────┐              ┌──────────────┐
│tg_bridge │              │   tg_bridge  │
│ log tail │              │  message     │
│  mc_to_  │◄────RCON────►│   handler    │
│   tg()   │              │  tg_to_mc() │
└──────────┘              └──────────────┘
    │                          │
    └──────────┬───────────────┘
               │
         ┌─────▼──────┐
         │  Telegram  │
         │    Group   │
         │  (Forum)   │
         └────────────┘
```

#### Commands Flow:

```
User: /status
  │
  ▼
tg_bridge.py catches command
  │
  ▼
is_admin() check
  │
  ▼
RCON connects to Minecraft
  │
  ▼
Parse response (TPS, players, etc)
  │
  ▼
Format message with emojis
  │
  ▼
Send back to Telegram topic
```

---

### 4. **Backup System** (backup.sh)

```
Cron (3:00 AM)
    │
    ▼
backup.sh starts
    │
    ├─ Stop minecraft.service
    ├─ Create ZIP archive
    │  ├─ world/
    │  ├─ config/
    │  ├─ server.properties
    │  └─ player data
    │
    ├─ Upload to Google Drive (rclone)
    │
    ├─ Delete backups older than 7 days
    │
    └─ Start minecraft.service
    
Notifications: Sent to LOG_TOPIC_ID
```

---

### 5. **Configuration System** (.env)

```
.env (secret, mode 600)
  ├─ Telegram (TG_TOKEN, TG_CHAT_ID)
  ├─ Minecraft (RCON_HOST, RCON_PORT, RCON_PASSWORD)
  ├─ Logging (LOG_FILE, LOG_TOPIC_ID)
  ├─ Backup (BACKUP_REMOTE, BACKUP_RETENTION_DAYS)
  └─ Admin (ADMIN_IDS, TOPIC_MAP)

.env.example (public template, no secrets)
  └─ Same structure but placeholder values
```

---

## Data Flow Diagrams

### **Chat Bridge (MC ↔ Telegram)**

```
Player types in Minecraft:
  "Hello from server!"

    │
    ▼
Server logs to /opt/minecraft/server-2/logs/latest.log

    │
    ▼
tg_bridge.py tail -f follows log

    │
    ▼
Regex matches: <PlayerName> Message

    │
    ▼
is_coordinate_text() check
  ├─ TRUE:  send to PIN_TOPIC_ID (coordinates topic)
  └─ FALSE: send to CHAT_TOPIC_ID (main chat topic)

    │
    ▼
Telegram receives formatted message:
  "[TG] PlayerName: Hello from server!"
```

### **Command Execution (Telegram → MC)**

```
Admin: /server restart

    │
    ▼
cmd_server() handler

    │
    ▼
is_admin(update) verification

    │
    ▼
systemctl restart minecraft.service

    │
    ▼
Wait 2 seconds for restart

    │
    ▼
get_service_state() check

    │
    ▼
Send response to Telegram:
  "✅ Server restart in progress..."
```

---

## File Organization

### GitHub Structure:
```
.
├── README.md              # Main project page
├── LICENSE                # MIT License
├── .gitignore            # What NOT to commit
│
├── docs/                 # Documentation
│   ├── QUICK_START.md    # 10-minute setup
│   ├── README.md         # Full reference
│   ├── MIGRATION.md      # New server setup
│   └── ARCHITECTURE.md   # This file
│
├── scripts/              # Executable scripts
│   ├── setup.sh          # One-click installation
│   └── backup.sh         # Backup automation
│
├── templates/            # Configuration templates
│   └── .env.example      # Environment template
│
├── config/               # Configuration examples
│   └── authme.yml        # AuthMe template (optional)
│
├── .github/              # GitHub-specific files
│   ├── workflows/        # CI/CD (optional)
│   └── ISSUE_TEMPLATE/   # Issue templates
│
└── src/                  # Source code
    └── tg_bridge.py      # Main bot code
```

### Server Structure (not in Git):
```
/opt/minecraft/
├── .env                  # SECRETS (gitignored)
├── server-2/             # ACTIVE SERVER (gitignored)
│   ├── paper-1.21.11-131.jar
│   ├── plugins/
│   ├── world/
│   └── logs/
└── backups/              # BACKUPS (gitignored)
    └── minecraft-*.zip
```

---

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Server** | Paper (Minecraft Fork) | 1.21.11 |
| **Java** | OpenJDK | 21+ |
| **Authentication** | AuthMe | 6.0.0 |
| **Bot Framework** | python-telegram-bot | latest |
| **RCON** | mcrcon | latest |
| **Backup Storage** | rclone + Google Drive | - |
| **Init System** | systemd | - |
| **Language** | Python 3 | 3.8+ |

---

## Security Model

```
┌─────────────────────────┐
│  Minecraft Server       │
│  (localhost:25565)      │◄─────── Players (encrypted)
└────────────┬────────────┘
             │
        RCON │ (localhost:25575)
             │ No external access
             │
             ▼
┌────────────────────────┐
│  tg_bridge.py          │
│  (RCON client)         │
└────────┬───────────────┘
         │
    Token│ (HTTPS)
         │
         ▼
    Telegram API
         │
         ▼
    Authorized Admin Users Only
```

---

## Performance Considerations

### **Java Heap Size**
```bash
-Xms512M  # Initial heap
-Xmx2G    # Maximum heap (adjust for your RAM)
```

### **G1GC Optimization**
```
Tuned for responsive gameplay:
- MaxGCPauseMillis: 200ms
- G1HeapRegionSize: 8M
- InitiatingHeapOccupancyPercent: 15%
```

### **Bot Efficiency**
```python
- Async message handling (non-blocking)
- Log tail (doesn't re-read entire log)
- RCON connection pooling
- Rate limiting on commands
```

### **Backup Impact**
```
- Server gracefully stopped (max 60 seconds)
- Parallel ZIP creation
- Incremental backups possible
- Cloud upload doesn't block restart
```

---

## Scaling Considerations

### **Single Server (Current)**
- Up to ~20-30 concurrent players
- 2GB heap sufficient

### **Multiple Servers**
- Each needs separate config (.env)
- Shared backup storage (Google Drive)
- Separate Telegram topics per server

### **Advanced Setup**
- Load balancer (nginx/haproxy)
- Centralized authentication (AuthMe network)
- Distributed backups
- Monitoring dashboards

---

**Last Updated:** 2026-05-16
