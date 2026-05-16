#!/bin/bash
# Minecraft + Telegram Bot Complete Setup Script
# Usage: sudo bash setup.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}🎮 Minecraft Server Setup${NC}"
echo -e "${BLUE}================================${NC}"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}❌ This script must be run as root (use: sudo bash setup.sh)${NC}"
   exit 1
fi

# Step 1: Install dependencies
echo -e "\n${YELLOW}Step 1: Installing dependencies...${NC}"
apt update
apt install -y openjdk-21-jre-headless git python3 python3-pip rclone zip curl wget
pip3 install mcrcon python-telegram-bot --break-system-packages

echo -e "${GREEN}✅ Dependencies installed${NC}"

# Step 2: Create directories
echo -e "\n${YELLOW}Step 2: Creating directories...${NC}"
mkdir -p /opt/minecraft/server-2/{plugins,logs,world,config}
mkdir -p /opt/minecraft/backups
mkdir -p /var/log/minecraft
cd /opt/minecraft

echo -e "${GREEN}✅ Directories created${NC}"

# Step 3: Get configuration from user
echo -e "\n${YELLOW}Step 3: Configuration Setup${NC}"
echo -e "${BLUE}Please provide the following information:${NC}"

read -p "$(echo -e ${BLUE}Telegram Bot Token (from BotFather): ${NC})" TG_TOKEN
read -p "$(echo -e ${BLUE}Telegram Chat ID (group/forum): ${NC})" TG_CHAT_ID
read -p "$(echo -e ${BLUE}CHAT Topic ID (default 6): ${NC})" CHAT_TOPIC_ID
CHAT_TOPIC_ID=${CHAT_TOPIC_ID:-6}
read -p "$(echo -e ${BLUE}LOG Topic ID (default 9555): ${NC})" LOG_TOPIC_ID
LOG_TOPIC_ID=${LOG_TOPIC_ID:-9555}
read -p "$(echo -e ${BLUE}Your Admin Telegram User ID: ${NC})" ADMIN_IDS
read -p "$(echo -e ${BLUE}RCON Password (for server.properties): ${NC})" RCON_PASSWORD

# Step 4: Create .env file
echo -e "\n${YELLOW}Step 4: Creating .env configuration...${NC}"

cat > /opt/minecraft/.env <<EOF
# Telegram Bot Configuration
TG_TOKEN=${TG_TOKEN}
TG_CHAT_ID=${TG_CHAT_ID}
CHAT_TOPIC_ID=${CHAT_TOPIC_ID}
LOG_TOPIC_ID=${LOG_TOPIC_ID}

# Minecraft RCON Configuration
RCON_HOST=localhost
RCON_PORT=25575
RCON_PASSWORD=${RCON_PASSWORD}

# Server Configuration
LOG_FILE=/opt/minecraft/server-2/logs/latest.log
MINECRAFT_SERVICE=minecraft
ADMIN_IDS=${ADMIN_IDS}

# Backup Configuration
BACKUP_SCRIPT=/opt/minecraft/backup.sh
BACKUP_DIR=/opt/minecraft/backups
BACKUP_REMOTE=gdrive:minecraft-backups/
BACKUP_RETENTION_DAYS=7

# Health Check Path
HEALTH_DISK_PATH=/opt/minecraft

# Topic Mapping (ID:NAME format, comma-separated)
TOPIC_MAP=6:CHAT,9555:LOG,2180:NEWS,1:GENERAL,26:GUIDE,1866:SCHEME,3505:PIN,1907:MOD,6141:MEME,29:PICS
EOF

chmod 600 /opt/minecraft/.env
echo -e "${GREEN}✅ .env file created${NC}"

# Step 5: Download Paper Server
echo -e "\n${YELLOW}Step 5: Downloading Paper Server 1.21.11...${NC}"
cd /opt/minecraft/server-2

if [ ! -f "paper-1.21.11-131.jar" ]; then
    echo "Downloading Paper 1.21.11 build 131..."
    wget -q https://api.papermc.io/v2/projects/paper/versions/1.21.11/builds/131/downloads/paper-1.21.11-131.jar
    echo -e "${GREEN}✅ Paper server downloaded${NC}"
else
    echo -e "${GREEN}✅ Paper server already exists${NC}"
fi

# Step 6: Accept EULA
echo -e "\n${YELLOW}Step 6: Accepting EULA...${NC}"
echo "eula=true" > /opt/minecraft/server-2/eula.txt
echo -e "${GREEN}✅ EULA accepted${NC}"

# Step 7: Configure server.properties
echo -e "\n${YELLOW}Step 7: Configuring server.properties...${NC}"
if [ -f "/opt/minecraft/server-2/server.properties" ]; then
    # Update RCON settings
    sed -i "s/enable-rcon=false/enable-rcon=true/" /opt/minecraft/server-2/server.properties
    sed -i "s/rcon.port=.*/rcon.port=25575/" /opt/minecraft/server-2/server.properties
    sed -i "s/rcon.password=.*/rcon.password=${RCON_PASSWORD}/" /opt/minecraft/server-2/server.properties
    echo -e "${GREEN}✅ server.properties updated${NC}"
fi

# Step 8: Download AuthMe Plugin
echo -e "\n${YELLOW}Step 8: Downloading AuthMe Plugin...${NC}"
if [ ! -f "/opt/minecraft/server-2/plugins/AuthMe-6.0.0-Paper.jar" ]; then
    mkdir -p /opt/minecraft/server-2/plugins
    wget -q -O /opt/minecraft/server-2/plugins/AuthMe-6.0.0-Paper.jar \
        https://github.com/AuthMe/AuthMeReloaded/releases/download/5.6.0-beta/AuthMe-6.0.0-Paper.jar
    echo -e "${GREEN}✅ AuthMe plugin downloaded${NC}"
else
    echo -e "${GREEN}✅ AuthMe plugin already exists${NC}"
fi

# Step 9: Create Systemd Services
echo -e "\n${YELLOW}Step 9: Creating systemd services...${NC}"

# Create minecraft user
if ! id "minecraft" &>/dev/null; then
    useradd -r -s /bin/bash minecraft
    echo -e "${GREEN}✅ minecraft user created${NC}"
fi

# Fix permissions
chown -R minecraft:minecraft /opt/minecraft/server-2
chown -R minecraft:minecraft /opt/minecraft/backups

# Create minecraft.service
cat > /etc/systemd/system/minecraft.service <<'SVCEOF'
[Unit]
Description=Minecraft Paper Server
After=network.target

[Service]
User=minecraft
WorkingDirectory=/opt/minecraft/server-2
ExecStart=/usr/bin/java -Xms512M -Xmx2G \
  -XX:+UseG1GC \
  -XX:+ParallelRefProcEnabled \
  -XX:MaxGCPauseMillis=200 \
  -XX:+UnlockExperimentalVMOptions \
  -XX:+DisableExplicitGC \
  -XX:+AlwaysPreTouch \
  -XX:G1NewSizePercent=30 \
  -XX:G1MaxNewSizePercent=40 \
  -XX:G1HeapRegionSize=8M \
  -XX:G1ReservePercent=20 \
  -XX:G1HeapWastePercent=5 \
  -XX:G1MixedGCCountTarget=4 \
  -XX:InitiatingHeapOccupancyPercent=15 \
  -XX:G1MixedGCLiveThresholdPercent=90 \
  -XX:G1RSetUpdatingPauseTimePercent=5 \
  -XX:SurvivorRatio=32 \
  -XX:+PerfDisableSharedMem \
  -XX:MaxTenuringThreshold=1 \
  -jar paper-1.21.11-131.jar nogui
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SVCEOF

# Create mc-tgbridge.service
cat > /etc/systemd/system/mc-tgbridge.service <<'SVCEOF'
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
SVCEOF

systemctl daemon-reload
echo -e "${GREEN}✅ Systemd services created${NC}"

# Step 10: Configure rclone (optional)
echo -e "\n${YELLOW}Step 10: Google Drive Backup Setup (Optional)${NC}"
read -p "Do you want to setup Google Drive backups? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Running: rclone config"
    echo "Make sure to:"
    echo "1. Choose 'N' (new remote)"
    echo "2. Name it 'gdrive'"
    echo "3. Choose 'Google Drive' (option 13 or similar)"
    echo "4. Follow OAuth authentication"
    rclone config
    echo -e "${GREEN}✅ rclone configured${NC}"
else
    echo -e "${YELLOW}⚠️ Skipping Google Drive setup. Update BACKUP_REMOTE in .env later.${NC}"
fi

# Step 11: Enable and start services
echo -e "\n${YELLOW}Step 11: Enabling and starting services...${NC}"
systemctl enable minecraft.service mc-tgbridge.service
systemctl start minecraft.service
sleep 5
systemctl start mc-tgbridge.service

echo -e "${GREEN}✅ Services started${NC}"

# Step 12: Create backup cron
echo -e "\n${YELLOW}Step 12: Setting up automated backups...${NC}"
cat > /etc/cron.d/minecraft-backup <<'CRONEOF'
# Minecraft daily backup at 3:00 AM
0 3 * * * root /opt/minecraft/backup.sh >> /var/log/minecraft-backup.log 2>&1
CRONEOF

echo -e "${GREEN}✅ Cron backup scheduled${NC}"

# Summary
echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo -e "${GREEN}================================${NC}"

echo -e "\n${BLUE}Next Steps:${NC}"
echo "1. Check service status:"
echo -e "   ${YELLOW}systemctl status minecraft.service${NC}"
echo "   ${YELLOW}systemctl status mc-tgbridge.service${NC}"
echo ""
echo "2. Check server logs:"
echo -e "   ${YELLOW}tail -f /opt/minecraft/server-2/logs/latest.log${NC}"
echo ""
echo "3. Wait for server to generate world (1-2 minutes)"
echo ""
echo "4. Test Telegram bot with: ${YELLOW}/status${NC} command"
echo ""
echo "5. Configure AuthMe (automatic, check game login)"
echo ""
echo -e "${BLUE}Configuration file: /opt/minecraft/.env${NC}"
echo -e "${BLUE}Backup location: /opt/minecraft/backups${NC}"
echo ""
echo "Happy gaming! 🎮"
