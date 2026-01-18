#!/usr/bin/env python3
"""
Open_Ai_Amir Сервер - Исправленная версия
"""

import http.server
import socketserver
import webbrowser
import json
import os
import requests

PORT = 8888
KOBOLD_URL = "http://localhost:5001/v1/chat/completions"

# Загружаем промпт
def load_system_prompt():
    try:
        with open('system_prompt.txt', 'r', encoding='utf-8') as f:
            return f.read().strip()
    except:
        return "ТЫ - Open_Ai_Amir, полезный ИИ-ассистент созданный Амирханом."

SYSTEM_PROMPT = load_system_prompt()

class AIRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = f"""<!DOCTYPE html>
            <html>
            <head><title>🤖 Open_Ai_Amir</title></head>
            <body style="font-family:Arial; background:#0f172a; color:white; padding:20px;">
                <h1>🤖 Open_Ai_Amir</h1>
                <p>Создатель: <strong>Амирхан</strong></p>
                <div id="chat"></div>
                <input id="msg" placeholder="Сообщение...">
                <button onclick="send()">Отправить</button>
                <script>
                    async function send() {{
                        const msg = document.getElementById('msg').value;
                        const res = await fetch('/chat', {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/json'}},
                            body: JSON.stringify({{message: msg}})
                        }});
                        const data = await res.json();
                        document.getElementById('chat').innerHTML += '<p>🤖: ' + data.reply + '</p>';
                    }}
                </script>
            </body>
            </html>"""
            
            self.wfile.write(html.encode('utf-8'))
            
        elif self.path == '/check_kobold':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            try:
                response = requests.get("http://localhost:5001", timeout=5)
                status = response.status_code == 200
            except:
                status = False
            
            self.wfile.write(json.dumps({"kobold_running": status}).encode('utf-8'))
    
    def do_POST(self):
        if self.path == '/chat':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            try:
                # УВЕЛИЧЕННЫЙ ТАЙМАУТ!
                response = requests.post(
                    KOBOLD_URL,
                    json={
                        "model": "llama-3.2-3b",
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": data.get('message', '')}
                        ],
                        "max_tokens": 500,
                        "temperature": 0.7
                    },
                    timeout=120  # ← 2 МИНУТЫ!
                )
                
                result = response.json()
                reply = result['choices'][0]['message']['content']
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"reply": reply}).encode('utf-8'))
                
            except Exception as e:
                print(f"Ошибка: {e}")
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "reply": f"Ошибка сервера: {str(e)}"
                }).encode('utf-8'))

def start_server():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print(f"\n{'='*60}")
    print(f"🤖 Open_Ai_Amir Web Server (FIXED)")
    print(f"{'='*60}")
    print(f"🌐 Веб-сервер запущен: http://localhost:{PORT}")
    print(f"🤖 KoboldCpp API: {KOBOLD_URL}")
    print(f"{'='*60}")
    
    # Проверка KoboldCpp
    try:
        response = requests.get("http://localhost:5001", timeout=5)
        if response.status_code == 200:
            print("✅ KoboldCpp запущен и работает!")
        else:
            print("⚠️ KoboldCpp отвечает, но с ошибкой")
    except:
        print("❌ KoboldCpp не запущен!")
    
    print(f"\n🚀 Открываю браузер...")
    webbrowser.open(f"http://localhost:{PORT}")
    print(f"\n🔄 Сервер работает. Нажми Ctrl+C для остановки\n")
    
    with socketserver.TCPServer(("", PORT), AIRequestHandler) as httpd:
        httpd.serve_forever()

if __name__ == "__main__":
    start_server()