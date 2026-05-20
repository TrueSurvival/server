// ============================================
// MINECRAFT SERVER PORTAL - MAIN JAVASCRIPT
// ============================================

// DOM Elements
const navLinks = document.querySelectorAll('.nav-link');
const pages = document.querySelectorAll('.page');
const themeToggle = document.querySelector('.theme-toggle');
const body = document.body;

// ============================================
// PAGE NAVIGATION
// ============================================

navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        
        // Remove active class from all links
        navLinks.forEach(l => l.classList.remove('active'));
        
        // Add active class to clicked link
        link.classList.add('active');
        
        // Get page name
        const pageName = link.getAttribute('href').substring(1) || 'home';
        
        // Hide all pages
        pages.forEach(page => page.classList.remove('active'));
        
        // Show selected page
        const selectedPage = document.getElementById(pageName);
        if (selectedPage) {
            selectedPage.classList.add('active');
            window.scrollTo(0, 0);
        }
    });
});

// Set home as active by default
document.querySelector('a[href="#home"]').classList.add('active');
document.getElementById('home').classList.add('active');

// ============================================
// THEME TOGGLE
// ============================================

function toggleTheme() {
    const isDark = body.classList.contains('dark-theme');
    
    if (isDark) {
        body.classList.remove('dark-theme');
        body.classList.add('light-theme');
        themeToggle.textContent = '☀️ Light';
        localStorage.setItem('theme', 'light');
    } else {
        body.classList.remove('light-theme');
        body.classList.add('dark-theme');
        themeToggle.textContent = '🌙 Dark';
        localStorage.setItem('theme', 'dark');
    }
}

themeToggle.addEventListener('click', toggleTheme);

// Load saved theme
window.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    if (savedTheme === 'light') {
        body.classList.remove('dark-theme');
        body.classList.add('light-theme');
        themeToggle.textContent = '☀️ Light';
    }
});

// ============================================
// SERVER STATUS UPDATE
// ============================================

async function updateServerStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        // Update status elements
        const statusEl = document.getElementById('status');
        const playersEl = document.getElementById('players');
        const memoryEl = document.getElementById('memory');
        const cpuEl = document.getElementById('cpu');
        const worldSizeEl = document.getElementById('worldsize');
        const statusBadge = document.getElementById('statusBadge');
        const lastUpdateEl = document.getElementById('lastUpdate');
        
        if (statusEl) statusEl.textContent = data.server.online ? '🟢 Online' : '🔴 Offline';
        if (playersEl) playersEl.textContent = `${data.server.players}/${data.server.max_players}`;
        if (memoryEl) memoryEl.textContent = data.server.memory;
        if (cpuEl) cpuEl.textContent = data.server.cpu;
        if (worldSizeEl) worldSizeEl.textContent = data.worlds.overworld || 'N/A';
        if (lastUpdateEl) lastUpdateEl.textContent = new Date().toLocaleTimeString();
        
        // Update badge
        if (statusBadge) {
            if (data.server.online) {
                statusBadge.className = 'status-badge online';
                statusBadge.innerHTML = '🟢 ONLINE';
                statusBadge.style.animation = 'pulse 2s ease-in-out infinite';
            } else {
                statusBadge.className = 'status-badge offline';
                statusBadge.innerHTML = '🔴 OFFLINE';
            }
        }
    } catch (error) {
        console.error('Status update failed:', error);
    }
}

// Update status every 5 seconds
setInterval(updateServerStatus, 5000);
updateServerStatus();

// ============================================
// LIVE LOGS UPDATE
// ============================================

async function updateLogs() {
    try {
        const response = await fetch('/api/logs');
        const data = await response.json();
        const container = document.getElementById('logsContainer');
        
        if (!container) return;
        
        container.innerHTML = '';
        
        data.logs.slice(-50).forEach(line => {
            if (line.trim()) {
                const logLine = document.createElement('div');
                logLine.className = 'log-line';
                
                if (line.includes('ERROR') || line.includes('FATAL')) {
                    logLine.classList.add('error');
                } else if (line.includes('WARN')) {
                    logLine.classList.add('warning');
                } else if (line.includes('joined') || line.includes('logged')) {
                    logLine.classList.add('success');
                }
                
                logLine.textContent = line.substring(0, 150);
                container.appendChild(logLine);
            }
        });
    } catch (error) {
        console.error('Log update failed:', error);
    }
}

// Update logs every 10 seconds
setInterval(updateLogs, 10000);
updateLogs();

// ============================================
// TABS FUNCTIONALITY
// ============================================

const tabBtns = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const tabId = btn.getAttribute('data-tab');
        
        // Remove active from all
        tabBtns.forEach(b => b.classList.remove('active'));
        tabContents.forEach(c => c.classList.remove('active'));
        
        // Add active to clicked
        btn.classList.add('active');
        document.getElementById(tabId)?.classList.add('active');
    });
});

// ============================================
// SMOOTH SCROLLING
// ============================================

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        if (href !== '#' && !href.startsWith('#page-')) {
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        }
    });
});

// ============================================
// ANIMATIONS ON SCROLL
// ============================================

const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.animation = 'slideUp 0.6s ease-out forwards';
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

// Observe cards
document.querySelectorAll('.card').forEach(card => {
    observer.observe(card);
});

// ============================================
// COPY CODE BLOCKS
// ============================================

document.querySelectorAll('.code-block').forEach(block => {
    const btn = document.createElement('button');
    btn.textContent = '📋 Copy';
    btn.style.cssText = `
        position: absolute;
        top: 10px;
        right: 10px;
        background: var(--accent);
        color: var(--primary);
        border: none;
        padding: 8px 15px;
        border-radius: 5px;
        cursor: pointer;
        font-size: 12px;
        font-weight: 600;
        z-index: 10;
    `;
    
    block.style.position = 'relative';
    block.parentElement.insertBefore(btn, block.nextSibling);
    
    btn.addEventListener('click', () => {
        const code = block.textContent;
        navigator.clipboard.writeText(code).then(() => {
            btn.textContent = '✅ Copied!';
            setTimeout(() => btn.textContent = '📋 Copy', 2000);
        });
    });
});

// ============================================
// PARTICLE EFFECT (Optional)
// ============================================

function createParticle(x, y) {
    const particle = document.createElement('div');
    particle.style.cssText = `
        position: fixed;
        left: ${x}px;
        top: ${y}px;
        width: 10px;
        height: 10px;
        background: var(--accent);
        border-radius: 50%;
        pointer-events: none;
        z-index: 9999;
        opacity: 0.8;
        animation: fadeOut 1s forwards;
    `;
    
    document.body.appendChild(particle);
    
    setTimeout(() => particle.remove(), 1000);
}

// Add particle effect on clicks
// document.addEventListener('click', (e) => {
//     if (e.target.closest('button, a')) {
//         createParticle(e.clientX, e.clientY);
//     }
// });

// ============================================
// CONSOLE MESSAGE
// ============================================

console.log('%c🎮 MC.SODOPS.UZ', 'color: #00d084; font-size: 20px; font-weight: bold;');
console.log('%cMinecraft Server Portal v1.0', 'color: #00d084; font-size: 14px;');
console.log('%cDeveloper: Sodiq | © 2026', 'color: #b0b0b0; font-size: 12px;');

// ============================================
// PERFORMANCE MONITORING
// ============================================

let lastUpdateTime = Date.now();
setInterval(() => {
    const currentTime = Date.now();
    const fps = Math.round(1000 / (currentTime - lastUpdateTime));
    lastUpdateTime = currentTime;
}, 1000);

// ============================================
// KEYBOARD SHORTCUTS
// ============================================

document.addEventListener('keydown', (e) => {
    // Alt + T = Toggle Theme
    if (e.altKey && e.key === 't') {
        e.preventDefault();
        toggleTheme();
    }
    
    // Alt + H = Home
    if (e.altKey && e.key === 'h') {
        e.preventDefault();
        document.querySelector('a[href="#home"]').click();
    }
});

// ============================================
// UTILITY FUNCTIONS
// ============================================

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function getTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    let interval = seconds / 31536000;
    if (interval > 1) return Math.floor(interval) + ' years ago';
    interval = seconds / 2592000;
    if (interval > 1) return Math.floor(interval) + ' months ago';
    interval = seconds / 86400;
    if (interval > 1) return Math.floor(interval) + ' days ago';
    interval = seconds / 3600;
    if (interval > 1) return Math.floor(interval) + ' hours ago';
    interval = seconds / 60;
    if (interval > 1) return Math.floor(interval) + ' minutes ago';
    return Math.floor(seconds) + ' seconds ago';
}

// Export for use in other scripts
window.PortalUtils = {
    formatBytes,
    getTimeAgo,
    updateServerStatus,
    updateLogs
};
