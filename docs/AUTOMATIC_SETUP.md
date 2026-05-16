# 🤖 Automatic Setup Guide

`setup.sh` can now run in **two modes:**

## Mode 1: Interactive (User-Friendly) ✅

```bash
sudo bash setup.sh
```

**Works as before:**
- Prompts for Telegram token, Chat ID, RCON password
- Asks if you want to setup Google Drive
- Everything is explained step-by-step

---

## Mode 2: Fully Automatic (CI/CD Ready) 🚀

Set environment variables **before** running script:

```bash
export TG_TOKEN="YOUR_BOT_TOKEN_HERE"
export TG_CHAT_ID="-1001234567890"
export ADMIN_IDS="123456789"
export RCON_PASSWORD="your_secure_password"
export CHAT_TOPIC_ID="6"                    # optional, default: 6
export LOG_TOPIC_ID="9555"                  # optional, default: 9555
export AUTO_RCLONE="skip"                   # optional: skip Google Drive setup

sudo -E bash setup.sh
```

**-E flag:** Preserves environment variables when using `sudo`

---

## Example: One-Line Automatic Deploy

```bash
export TG_TOKEN="7236829228:AAH5190wnRjsBOa6YKaoIO6glLfgBi2gh5A" && \
export TG_CHAT_ID="-1001914112188" && \
export ADMIN_IDS="6984554888" && \
export RCON_PASSWORD="02282006Sodiq" && \
export AUTO_RCLONE="skip" && \
sudo -E bash setup.sh
```

**Result:** 100% automatic, no user prompts!

---

## For CI/CD Pipelines

Create `.env.setup` with your config:

```bash
#!/bin/bash
export TG_TOKEN="your_token"
export TG_CHAT_ID="your_chat_id"
export ADMIN_IDS="your_admin_id"
export RCON_PASSWORD="your_password"
export AUTO_RCLONE="skip"
```

Then deploy:

```bash
source .env.setup
sudo -E bash setup.sh
```

---

## Environment Variables Reference

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `TG_TOKEN` | ✅ YES | - | Telegram bot token from BotFather |
| `TG_CHAT_ID` | ✅ YES | - | Telegram group/forum ID (negative number) |
| `ADMIN_IDS` | ✅ YES | - | Your Telegram user ID (admin) |
| `RCON_PASSWORD` | ✅ YES | - | Server RCON password |
| `CHAT_TOPIC_ID` | ❌ NO | 6 | Telegram topic for chat messages |
| `LOG_TOPIC_ID` | ❌ NO | 9555 | Telegram topic for server logs |
| `AUTO_RCLONE` | ❌ NO | - | Set to "skip" to skip Google Drive setup |

---

## Getting Your Configuration Values

### 📱 Telegram Bot Token
1. Open [@BotFather](https://t.me/botfather)
2. `/newbot`
3. Follow instructions → get `TG_TOKEN`

### 💬 Chat ID & Admin ID
1. Send any message in your Telegram forum/group
2. Forward to [@userinfobot](https://t.me/userinfobot)
3. Shows `ChatID` (use for `TG_CHAT_ID`)
4. Your ID is shown as `UserID` (use for `ADMIN_IDS`)

### 🔐 RCON Password
- Create a strong password for server access
- Will be stored in `.env` (mode 600, encrypted)

---

## What Happens in Each Mode

### Interactive Mode:
```
1. Asks for Telegram token ← You type it
2. Asks for Chat ID ← You type it
3. Asks for Admin ID ← You type it
4. Asks for RCON password ← You type it
5. (Optional) Asks about Google Drive ← You choose y/n
6. Installs everything
7. Done! ✅
```

### Automatic Mode:
```
1. Reads TG_TOKEN from environment ✓
2. Reads TG_CHAT_ID from environment ✓
3. Reads ADMIN_IDS from environment ✓
4. Reads RCON_PASSWORD from environment ✓
5. Skips rclone (no prompts) ✓
6. Installs everything
7. Done! ✅ (Zero user interaction)
```

---

## Docker Example (Fully Automatic)

```dockerfile
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    openjdk-21-jre-headless \
    git \
    python3 \
    python3-pip \
    rclone \
    zip \
    curl \
    wget

WORKDIR /opt/minecraft

COPY setup.sh .

ENV TG_TOKEN=${TG_TOKEN} \
    TG_CHAT_ID=${TG_CHAT_ID} \
    ADMIN_IDS=${ADMIN_IDS} \
    RCON_PASSWORD=${RCON_PASSWORD} \
    AUTO_RCLONE=skip

RUN chmod +x setup.sh && \
    bash setup.sh   # No sudo needed in Docker

EXPOSE 25565 25575

CMD ["systemctl", "start", "minecraft.service"]
```

Run:
```bash
docker build \
  --build-arg TG_TOKEN="your_token" \
  --build-arg TG_CHAT_ID="your_chat_id" \
  --build-arg ADMIN_IDS="your_admin_id" \
  --build-arg RCON_PASSWORD="your_password" \
  -t minecraft-server .
```

---

## Kubernetes Example

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: minecraft-config
data:
  setup.sh: |
    #!/bin/bash
    export TG_TOKEN="from-secret"
    export TG_CHAT_ID="-1001234567890"
    export ADMIN_IDS="6984554888"
    export RCON_PASSWORD="from-secret"
    export AUTO_RCLONE="skip"
    bash /scripts/setup.sh
---
apiVersion: v1
kind: Pod
metadata:
  name: minecraft-server
spec:
  containers:
  - name: minecraft
    image: ubuntu:22.04
    env:
    - name: TG_TOKEN
      valueFrom:
        secretKeyRef:
          name: minecraft-secrets
          key: tg-token
    - name: TG_CHAT_ID
      valueFrom:
        configMapKeyRef:
          name: minecraft-config
          key: chat-id
    # ... more env vars
    command: ["bash", "/scripts/setup.sh"]
```

---

## Troubleshooting Automatic Setup

### "Command not found" error?
Make sure `-E` flag is used with sudo:
```bash
sudo -E bash setup.sh
# NOT: sudo bash setup.sh
```

### Variables not being read?
Check if they're exported:
```bash
echo $TG_TOKEN
# Should show your token, not empty
```

### Need to verify config before running?
```bash
echo "TG_TOKEN: $TG_TOKEN"
echo "TG_CHAT_ID: $TG_CHAT_ID"
echo "ADMIN_IDS: $ADMIN_IDS"
echo "RCON_PASSWORD: ****"
```

---

## After Setup Completes

Whether automatic or interactive:

1. ✅ Minecraft server installed
2. ✅ AuthMe plugin configured
3. ✅ systemd services created
4. ✅ Telegram bot linked
5. ✅ Backups scheduled

**Check status:**
```bash
systemctl status minecraft.service
systemctl status mc-tgbridge.service
tail -f /opt/minecraft/server-2/logs/latest.log
```

**Test bot:**
```
Send: /status
Receive: Server status ✓
```

---

## Quick Reference: Copy-Paste Commands

### For Ubuntu 22.04 Server:
```bash
# 1. Clone project
git clone https://github.com/YOUR_USERNAME/minecraft-telegram-bot.git /opt/minecraft
cd /opt/minecraft

# 2. Set your config (replace with YOUR values)
export TG_TOKEN="7236829228:AAH5190wnRjsBOa6YKaoIO6glLfgBi2gh5A"
export TG_CHAT_ID="-1001914112188"
export ADMIN_IDS="6984554888"
export RCON_PASSWORD="02282006Sodiq"
export AUTO_RCLONE="skip"

# 3. Run automatic setup
sudo -E bash setup.sh

# 4. Done! Server is running
systemctl status minecraft.service
```

---

**setup.sh now supports both interactive AND automatic modes! Choose what suits you best. 🚀**
