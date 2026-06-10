#!/usr/bin/env node

const mineflayer = require('mineflayer');
const pathfinder = require('mineflayer-pathfinder');
const { goals } = pathfinder;
const fs = require('fs');

// Configuration
const CONFIG = {
    host: process.env.MC_HOST || 'localhost',
    port: parseInt(process.env.MC_PORT || '25565'),
    username: process.env.BOT_USERNAME || 'AFKBot',
    auth: 'offline',
    version: '1.21.11',
    x: parseFloat(process.env.AFK_X || '0'),
    y: parseFloat(process.env.AFK_Y || '65'),
    z: parseFloat(process.env.AFK_Z || '0'),
    logFile: process.env.LOG_FILE || '/opt/minecraft/afk-bot/afk-bot.log'
};

// Logger
const logger = {
    log: (msg) => {
        const timestamp = new Date().toISOString();
        const logMsg = `[${timestamp}] ${msg}`;
        console.log(logMsg);
        try {
            fs.appendFileSync(CONFIG.logFile, logMsg + '\n');
        } catch (e) {
            console.error('Log write error:', e.message);
        }
    },
    error: (msg) => logger.log(`[ERROR] ${msg}`),
    info: (msg) => logger.log(`[INFO] ${msg}`),
    success: (msg) => logger.log(`[SUCCESS] ${msg}`)
};

logger.info(`Starting AFK Bot...`);
logger.info(`Server: ${CONFIG.host}:${CONFIG.port}`);
logger.info(`Username: ${CONFIG.username}`);
logger.info(`AFK Location: x=${CONFIG.x}, y=${CONFIG.y}, z=${CONFIG.z}`);

// Create bot
const bot = mineflayer.createBot({
    host: CONFIG.host,
    port: CONFIG.port,
    username: CONFIG.username,
    auth: 'offline',
    version: '1.21.11'
});

let isConnected = false;
let afkLoopInterval = null;
let reconnectAttempts = 0;
const MAX_RECONNECT = 10;

// Login event
bot.on('login', () => {
    logger.success(`Logged in as ${bot.username}`);
    isConnected = true;
    reconnectAttempts = 0;
    
    // Load pathfinder plugin
    bot.loadPlugin(pathfinder.pathfinder);
    
    setTimeout(() => teleportToAFK(), 2000);
});

// Spawn event
let hasAuthenticated = false;

bot.on('spawn', () => {
    logger.info('Spawned, ready to AFK');
    
    // Auto-login/register if not already authenticated
    if (!hasAuthenticated) {
        setTimeout(() => {
            logger.info('Authenticating...');
            // Try login first, if fails try register
            bot.chat('/login AFKBot123');
            hasAuthenticated = true;
            setTimeout(() => teleportToAFK(), 1500);
        }, 500);
    }
});

// Disconnect
bot.on('end', (reason) => {
    logger.error(`Disconnected: ${reason}`);
    isConnected = false;
    stopAFKLoop();
    
    if (reconnectAttempts < MAX_RECONNECT) {
        reconnectAttempts++;
        logger.info(`Reconnecting (${reconnectAttempts}/${MAX_RECONNECT})...`);
        setTimeout(() => {
            try {
                bot._client.connect();
            } catch (e) {
                logger.error(`Reconnect error: ${e.message}`);
            }
        }, 5000);
    } else {
        logger.error('Max reconnections reached. Exiting.');
        process.exit(1);
    }
});

// Errors
bot.on('error', (err) => {
    logger.error(`Error: ${err.message}`);
});

bot.on('kicked', (reason) => {
    logger.error(`Kicked: ${reason}`);
});

// Chat
bot.on('message', (msg) => {
    const plainMsg = msg.toString();
    if (!plainMsg.includes(bot.username)) {
        logger.info(`Chat: ${plainMsg}`);
    }
});

// AFK Loop
function startAFKLoop() {
    if (afkLoopInterval) clearInterval(afkLoopInterval);
    
    afkLoopInterval = setInterval(() => {
        if (!isConnected || !bot.entity) return;
        
        try {
            // Rotate view
            const yaw = Math.random() * Math.PI * 2;
            const pitch = (Math.random() - 0.5) * Math.PI * 0.5;
            bot.look(yaw, pitch, false);
            
            // Occasional movement
            if (Math.random() > 0.7) {
                const duration = 100 + Math.random() * 200;
                bot.setControlState('forward', true);
                setTimeout(() => bot.setControlState('forward', false), duration);
            }
            
            logger.info(`AFK rotation: yaw=${yaw.toFixed(2)}, pitch=${pitch.toFixed(2)}`);
        } catch (e) {
            logger.error(`AFK loop error: ${e.message}`);
        }
    }, 30000);
}

function stopAFKLoop() {
    if (afkLoopInterval) {
        clearInterval(afkLoopInterval);
        afkLoopInterval = null;
    }
}

// Teleport to AFK location
function teleportToAFK() {
    if (!isConnected || !bot.entity) {
        logger.error('Cannot teleport: not connected or no entity');
        return;
    }
    
    const pos = bot.entity.position;
    logger.info(`Current: x=${pos.x.toFixed(1)}, y=${pos.y.toFixed(1)}, z=${pos.z.toFixed(1)}`);
    logger.info(`Teleporting to: x=${CONFIG.x}, y=${CONFIG.y}, z=${CONFIG.z}`);
    
    try {
        // Use pathfinder to move to target location
        if (bot.pathfinder) {
            const goal = new goals.GoalBlock(CONFIG.x, CONFIG.y - 1, CONFIG.z);
            bot.pathfinder.setGoal(goal);
            
            setTimeout(() => {
                if (bot.pathfinder) {
                    bot.pathfinder.stop();
                }
                const newPos = bot.entity.position;
                logger.success(`Reached AFK location: x=${newPos.x.toFixed(1)}, y=${newPos.y.toFixed(1)}, z=${newPos.z.toFixed(1)}`);
                startAFKLoop();
            }, 3000);
        } else {
            // Fallback: direct command if pathfinder not loaded
            logger.info('Pathfinder not ready, using teleport command...');
            bot.chat(`/tp @s ${CONFIG.x} ${CONFIG.y} ${CONFIG.z}`);
            setTimeout(() => startAFKLoop(), 1000);
        }
    } catch (e) {
        logger.error(`Teleport error: ${e.message}`);
        startAFKLoop();
    }
}

// Graceful shutdown
process.on('SIGINT', () => {
    logger.info('Shutting down...');
    stopAFKLoop();
    bot.quit();
    process.exit(0);
});

process.on('SIGTERM', () => {
    logger.info('Shutting down...');
    stopAFKLoop();
    bot.quit();
    process.exit(0);
});

logger.info('Connecting to server...');
