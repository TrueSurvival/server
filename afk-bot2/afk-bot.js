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
    
    // Don't teleport - user will manually place bot and TP
    // setTimeout(() => teleportToAFK(), 2000);
});

// Spawn event
let hasAuthenticated = false;

bot.on('spawn', () => {
    logger.info('Spawned, ready to AFK');
    
    // Auto-login/register if not already authenticated
    if (!hasAuthenticated) {
        setTimeout(() => {
            logger.info('Authenticating...');
            // Try login first
            bot.chat('/login AFKBot2123');
            hasAuthenticated = true;
            // Don't teleport - user will do it manually
            // setTimeout(() => teleportToAFK(), 1500);
            // Start AFK immediately
            setTimeout(() => startAFKLoop(), 1500);
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
    
    // Skip join/leave notifications
    if (plainMsg.includes('joined the game') || plainMsg.includes('left the game')) {
        return;
    }
    
    logger.info(`Chat: ${plainMsg}`);
    
    // Auto-register if not registered
    if (plainMsg.includes("isn't registered")) {
        logger.info('Attempting auto-register...');
        setTimeout(() => {
            bot.chat('/register AFKBot2123 AFKBot2123');
        }, 500);
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
            
            // Jump occasionally to prevent AFK detection
            if (Math.random() > 0.6) {
                bot.setControlState('jump', true);
                setTimeout(() => bot.setControlState('jump', false), 100);
            }
            
            // Find and attack zombified piglin
            attackZombifiedPiglin();
            
            logger.info(`AFK rotation: yaw=${yaw.toFixed(2)}, pitch=${pitch.toFixed(2)}`);
        } catch (e) {
            logger.error(`AFK loop error: ${e.message}`);
        }
    }, 30000);
}

// Attack nearby zombified piglin
function attackZombifiedPiglin() {
    if (!bot.entity) return;
    
    try {
        // Find all entities nearby
        const targets = Object.values(bot.entities)
            .filter(e => {
                // Check if entity is zombified piglin
                if (!e.name) return false;
                const name = e.name.toLowerCase();
                return name.includes('zombie') && name.includes('piglin') || name === 'zombified_piglin';
            })
            .sort((a, b) => {
                // Sort by distance - closest first
                const distA = bot.entity.position.distanceTo(a.position);
                const distB = bot.entity.position.distanceTo(b.position);
                return distA - distB;
            });
        
        if (targets.length > 0) {
            const target = targets[0];
            const distance = bot.entity.position.distanceTo(target.position);
            
            if (distance < 5) {
                // Attack if close enough
                bot.attack(target);
                logger.info(`Attacking Zombified Piglin at distance ${distance.toFixed(1)}m`);
            }
        }
    } catch (e) {
        logger.error(`Attack error: ${e.message}`);
    }
}

function stopAFKLoop() {
    if (afkLoopInterval) {
        clearInterval(afkLoopInterval);
        afkLoopInterval = null;
    }
}

// Teleport to AFK location in Nether
function teleportToAFK() {
    if (!isConnected || !bot.entity) {
        logger.error('Cannot teleport: not connected or no entity');
        return;
    }
    
    const pos = bot.entity.position;
    logger.info(`Current: x=${pos.x.toFixed(1)}, y=${pos.y.toFixed(1)}, z=${pos.z.toFixed(1)}`);
    logger.info(`Teleporting to Nether: x=${CONFIG.x}, y=${CONFIG.y}, z=${CONFIG.z}`);
    
    try {
        // Teleport to AFK location using format: /tp player X Y Z
        bot.chat(`/tp ${bot.username} 254 243 90`);
        
        setTimeout(() => {
            if (bot.pathfinder) {
                bot.pathfinder.stop();
            }
            const newPos = bot.entity.position;
            logger.success(`Teleported to Nether: x=${newPos.x.toFixed(1)}, y=${newPos.y.toFixed(1)}, z=${newPos.z.toFixed(1)}`);
            startAFKLoop();
        }, 2000);
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
