#!/usr/bin/env python3
"""
Minecraft Server Dynamic Web Portal
Real-time server status, player tracking, logs
Serves new professional HTML portal
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import subprocess
import socket
import os
import re
from datetime import datetime
from threading import Thread
import time
from mcrcon import MCRcon
import mimetypes
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/opt/minecraft/.env')

class MinecraftServerAPI:
    def __init__(self):
        self.host = os.getenv('RCON_HOST', 'localhost')
        self.port = int(os.getenv('MC_PORT', 25565))
        self.rcon_port = int(os.getenv('RCON_PORT', 25575))
        self.rcon_password = os.getenv('RCON_PASSWORD')
        self.server_path = os.getenv('SERVER_PATH', '/opt/minecraft/server-2')
        self.web_path = os.getenv('WEB_PATH', '/opt/minecraft/web')
        self.web_port = int(os.getenv('WEB_PORT', 8090))
        self.log_cache = []
        self.status_cache = {}
        self.last_update = 0
        self.player_count = 0
    
    def is_online(self):
        """Check if Minecraft server is online"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            return result == 0
        except:
            return False
    
    def get_player_count(self):
        """Get active player count via RCON"""
        try:
            mcr = MCRcon(self.host, self.rcon_password, port=self.rcon_port)
            mcr.connect()
            response = mcr.command("list")
            
            # Parse: "There are X of a max of Y players online:"
            match = re.search(r'There are (\d+) of a max of (\d+) players online', response)
            if match:
                current = int(match.group(1))
                max_players = int(match.group(2))
                self.player_count = current
                return {"current": current, "max": max_players}
            return {"current": 0, "max": 20}
        except Exception as e:
            # Fallback
            return {"current": self.player_count, "max": 20}
    
    def get_player_list(self):
        """Get list of online players"""
        try:
            mcr = MCRcon(self.host, self.rcon_password, port=self.rcon_port)
            mcr.connect()
            response = mcr.command("list")
            
            # Parse player names: "There are X of a max of Y players online: name1, name2, ..."
            if ":" in response:
                players_str = response.split(":")[-1].strip()
                if players_str:
                    return [p.strip() for p in players_str.split(",")]
            return []
        except:
            return []
    
    def get_tps(self):
        """Get server TPS (ticks per second) via Spark"""
        try:
            mcr = MCRcon(self.host, self.rcon_password, port=self.rcon_port)
            mcr.connect()
            response = mcr.command("spark tps")
            
            # Extract TPS numbers
            match = re.search(r'(\d+\.?\d*)\s*\/\s*(\d+\.?\d*)\s*\/\s*(\d+\.?\d*)', response)
            if match:
                return {
                    "1min": float(match.group(1)),
                    "5min": float(match.group(2)),
                    "15min": float(match.group(3))
                }
            return {"1min": 20, "5min": 20, "15min": 20}
        except:
            return {"1min": 20, "5min": 20, "15min": 20}
    
    def get_memory_usage(self):
        """Get server memory and CPU usage"""
        try:
            # Get process memory
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                timeout=5
            )
            for line in result.stdout.split('\n'):
                if 'server.jar' in line or 'paper' in line.lower():
                    parts = line.split()
                    if len(parts) >= 6:
                        try:
                            memory_mb = int(parts[5]) // 1024
                            cpu = float(parts[2])
                            return {
                                "memory": f"{memory_mb}MB / 2GB",
                                "cpu": f"{cpu:.1f}%"
                            }
                        except:
                            pass
            return {"memory": "N/A", "cpu": "N/A"}
        except:
            return {"memory": "N/A", "cpu": "N/A"}
    
    def get_world_size(self):
        """Get world file sizes"""
        try:
            worlds = {}
            server_dir = os.path.join(self.server_path, 'world')
            
            if os.path.exists(server_dir):
                size = 0
                for dirpath, dirnames, filenames in os.walk(server_dir):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        size += os.path.getsize(filepath)
                
                size_mb = size / (1024 * 1024)
                worlds['overworld'] = f"{size_mb:.2f}MB"
            
            return worlds
        except:
            return {"overworld": "N/A"}
    
    def get_uptime(self):
        """Get server uptime"""
        try:
            result = subprocess.run(
                ['ps', '-o', 'etime=', '-p', str(os.popen('pgrep -f server.jar').read().strip())],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.stdout:
                return result.stdout.strip()
            return "N/A"
        except:
            return "N/A"
    
    def get_logs(self):
        """Get server logs"""
        try:
            log_file = os.path.join(self.server_path, 'logs', 'latest.log')
            if not os.path.exists(log_file):
                return []
            
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                return [line.rstrip() for line in lines[-100:]]
        except:
            return []
    
    def get_full_status(self):
        """Get complete server status"""
        online = self.is_online()
        memory = self.get_memory_usage()
        worlds = self.get_world_size()
        uptime = self.get_uptime()
        players = self.get_player_count()
        player_list = self.get_player_list()
        tps = self.get_tps()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "server": {
                "name": "mc.sodops.uz",
                "online": online,
                "version": "1.21.11",
                "port": 25565,
                "players": players["current"],
                "max_players": players["max"],
                "player_list": player_list,
                "uptime": uptime,
                "memory": memory["memory"],
                "cpu": memory["cpu"],
                "tps": tps
            },
            "worlds": worlds,
            "motd": "Minecraft Survival Server"
        }

class RequestHandler(BaseHTTPRequestHandler):
    api = MinecraftServerAPI()
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            # API endpoints
            if self.path == '/api/status':
                self.send_json_response(self.api.get_full_status())
            elif self.path == '/api/logs':
                self.send_json_response({"logs": self.api.get_logs()})
            elif self.path == '/api/ping':
                self.send_json_response({"status": "pong"})
            elif self.path == '/api/players':
                self.send_json_response({
                    "players": self.api.get_player_list(),
                    "count": self.api.get_player_count()
                })
            elif self.path == '/api/tps':
                self.send_json_response({"tps": self.api.get_tps()})
            elif self.path == '/' or self.path == '/index.html':
                # Serve main HTML
                self.serve_file('/opt/minecraft/web/index.html', 'text/html')
            elif self.path == '/dashboard.html':
                # Serve dashboard
                self.serve_file('/opt/minecraft/web/dashboard.html', 'text/html')
            elif self.path.startswith('/assets/'):
                # Serve CSS, JS, etc
                file_path = '/opt/minecraft/web' + self.path
                mime_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
                self.serve_file(file_path, mime_type)
            else:
                # Try to serve any other HTML files from /opt/minecraft/web/
                if self.path.endswith('.html') or self.path.endswith('.css') or self.path.endswith('.js'):
                    file_path = '/opt/minecraft/web' + self.path
                    mime_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
                    self.serve_file(file_path, mime_type)
                else:
                    self.send_error(404)
        except Exception as e:
            print(f"Error: {e}")
            self.send_error(500)
    
    def serve_file(self, file_path, mime_type):
        """Serve a file"""
        try:
            if not os.path.exists(file_path):
                self.send_error(404)
                return
            
            with open(file_path, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', mime_type)
            self.send_header('Content-Length', len(content))
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            print(f"File serve error: {e}")
            self.send_error(500)
    
    def send_json_response(self, data):
        """Send JSON response"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        return

def run_server():
    """Start the web server"""
    api = MinecraftServerAPI()
    server_address = ('0.0.0.0', api.web_port)
    httpd = HTTPServer(server_address, RequestHandler)
    print(f"🌐 Web Server running on port {api.web_port}...")
    print(f"📊 Serving from: {api.web_path}")
    print(f"🎮 MC API enabled")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        httpd.server_close()

if __name__ == '__main__':
    run_server()
