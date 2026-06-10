#!/usr/bin/env python3
"""
Minecraft Server Status API - Simple HTTP Server
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import subprocess
import socket
from datetime import datetime

class ServerStatus:
    def __init__(self):
        self.host = "localhost"
        self.port = 25565
    
    def check_online(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            return result == 0
        except:
            return False
    
    def get_memory(self):
        try:
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True,
                timeout=3
            )
            for line in result.stdout.split('\n'):
                if 'paper' in line.lower() and 'jar' in line:
                    parts = line.split()
                    if len(parts) >= 6:
                        mb = int(parts[5]) / 1024
                        return f"{mb:.0f}MB"
            return "N/A"
        except:
            return "N/A"
    
    def get_status(self):
        return {
            "timestamp": datetime.now().isoformat(),
            "server": {
                "name": "mc.sodops.uz",
                "online": self.check_online(),
                "version": "1.21.11",
                "port": 25565,
                "memory": self.get_memory(),
                "players": 0,
                "max_players": 20
            }
        }

server_status = ServerStatus()

class APIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/status':
            status = server_status.get_status()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(status).encode())
        
        elif self.path == '/ping':
            status = "online" if server_status.check_online() else "offline"
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": status}).encode())
        
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8080), APIHandler)
    print("Minecraft Server API running on http://0.0.0.0:8080")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
        server.server_close()
