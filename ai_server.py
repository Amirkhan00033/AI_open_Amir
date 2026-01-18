#!/usr/bin/env python3
"""
Open_Ai_Amir Сервер - Связывает HTML интерфейс с ИИ
Создатель: Амирхан
"""

import http.server
import socketserver
import webbrowser
import threading
import json
import os
import time
from urllib.parse import urlparse, parse_qs
import requests

# ===== КОНФИГУРАЦИЯ =====
PORT = 8888  # Веб-сервер будет на этом порту
KOBOLD_URL = "http://localhost:5001/v1/chat/completions"  # KoboldCpp API

# ФИКСИРОВАННАЯ ЛИЧНОСТЬ ИИ - НИКОГДА НЕ МЕНЯЕТСЯ!
# ===== КОНФИГУРАЦИЯ =====
PORT = 8888  # Веб-сервер будет на этом порту
KOBOLD_URL = "http://localhost:5001/v1/chat/completions"  # KoboldCpp API

# ===== ЗАГРУЗКА ПРОМПТА ИЗ ФАЙЛА =====
def load_system_prompt():
    """Загружает системный промпт из файла"""
    try:
        with open('system_prompt.txt', 'r', encoding='utf-8') as f:
            prompt = f.read().strip()
            print(f"✅ Загружен промпт из system_prompt.txt ({len(prompt)} символов)")
            return prompt
    except FileNotFoundError:
        # Фолбэк если файла нет
        fallback_prompt = """ТЫ - Open_Ai_Amir, полезный ИИ-ассистент."""
        print(f"⚠️ Файл system_prompt.txt не найден, использую fallback промпт")
        return fallback_prompt
    except Exception as e:
        print(f"❌ Ошибка загрузки промпта: {e}")
        return """ТЫ - Open_Ai_Amir, полезный ИИ-ассистент."""

SYSTEM_PROMPT = load_system_prompt()

# ===== HTML ШАБЛОН =====
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 Open_Ai_Amir Чат</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0f172a, #1e293b);
            color: white;
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: rgba(30, 41, 59, 0.9);
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
            border: 3px solid #00ff88;
        }
        .header {
            background: linear-gradient(135deg, #1e40af, #1e3a8a);
            padding: 30px;
            text-align: center;
            border-bottom: 3px solid #00ff88;
        }
        .ai-name {
            font-size: 2.5rem;
            color: #00ff88;
            margin-bottom: 10px;
            text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
        }
        .creator {
            font-size: 1.2rem;
            color: #93c5fd;
        }
        .creator strong {
            color: #00ff88;
            font-size: 1.3rem;
        }
        .status {
            display: inline-block;
            background: #059669;
            color: white;
            padding: 8px 20px;
            border-radius: 20px;
            margin-top: 15px;
            font-weight: bold;
        }
        .chat-container {
            display: flex;
            height: 600px;
        }
        .sidebar {
            width: 300px;
            background: rgba(15, 23, 42, 0.9);
            padding: 25px;
            border-right: 2px solid #334155;
            overflow-y: auto;
        }
        .personality-box {
            background: rgba(6, 78, 59, 0.3);
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 25px;
            border-left: 4px solid #00ff88;
        }
        .personality-box h3 {
            color: #00ff88;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .personality-item {
            margin: 10px 0;
            padding-left: 25px;
            position: relative;
        }
        .personality-item:before {
            content: "🔒";
            position: absolute;
            left: 0;
            color: #00ff88;
        }
        .locked {
            color: #00ff88;
            font-weight: bold;
        }
        .chat-area {
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 25px;
            background: rgba(15, 23, 42, 0.7);
        }
        .message {
            margin: 15px 0;
            padding: 18px;
            border-radius: 18px;
            max-width: 85%;
            animation: fadeIn 0.4s;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }
        .user-message {
            background: linear-gradient(135deg, #3b82f6, #1d4ed8);
            margin-left: auto;
            border-bottom-right-radius: 5px;
            border-right: 4px solid #1d4ed8;
        }
        .bot-message {
            background: linear-gradient(135deg, #065f46, #047857);
            margin-right: auto;
            border-bottom-left-radius: 5px;
            border-left: 4px solid #00ff88;
        }
        .message-header {
            font-weight: bold;
            margin-bottom: 10px;
            font-size: 0.95rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .user-message .message-header {
            color: #bfdbfe;
        }
        .bot-message .message-header {
            color: #00ff88;
        }
        .message-content {
            font-size: 1.1rem;
            line-height: 1.6;
        }
        .input-area {
            padding: 25px;
            background: rgba(30, 41, 59, 0.95);
            border-top: 2px solid #334155;
        }
        .input-container {
            display: flex;
            gap: 15px;
        }
        #messageInput {
            flex: 1;
            padding: 18px 25px;
            border: none;
            border-radius: 30px;
            background: rgba(255, 255, 255, 0.1);
            color: white;
            font-size: 1.1rem;
            outline: none;
            transition: all 0.3s;
        }
        #messageInput:focus {
            background: rgba(255, 255, 255, 0.15);
            box-shadow: 0 0 0 3px rgba(0, 255, 136, 0.3);
        }
        #messageInput::placeholder {
            color: rgba(255, 255, 255, 0.5);
        }
        #sendButton {
            background: linear-gradient(135deg, #00ff88, #00cc6a);
            color: #002211;
            border: none;
            padding: 18px 35px;
            border-radius: 30px;
            cursor: pointer;
            font-weight: bold;
            font-size: 1.1rem;
            transition: all 0.3s;
            min-width: 140px;
        }
        #sendButton:hover {
            transform: scale(1.05);
            box-shadow: 0 10px 25px rgba(0, 255, 136, 0.4);
        }
        .typing-indicator {
            display: none;
            padding: 15px 25px;
            background: rgba(30, 41, 59, 0.9);
            border-radius: 25px;
            margin: 15px;
            width: fit-content;
        }
        .typing-dots {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        .typing-dots span {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #00ff88;
            animation: typing 1.4s infinite;
        }
        .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
        .typing-dots span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(15px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes typing {
            0%, 100% { transform: translateY(0); opacity: 0.4; }
            50% { transform: translateY(-8px); opacity: 1; }
        }
        @media (max-width: 900px) {
            .chat-container { flex-direction: column; height: auto; }
            .sidebar { width: 100%; border-right: none; border-bottom: 2px solid #334155; }
            .message { max-width: 95%; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="ai-name">🤖 Open_Ai_Amir</div>
            <div class="creator">Создатель: <strong>Амирхан</strong> | Личность ИИ защищена</div>
            <div class="status">● ОНЛАЙН | Порт: {port}</div>
        </div>
        
        <div class="chat-container">
            <div class="sidebar">
                <div class="personality-box">
                    <h3>🔒 Личность ИИ защищена</h3>
                    <div class="personality-item">Имя: <span class="locked">Open_Ai_Amir</span></div>
                    <div class="personality-item">Создатель: <span class="locked">Амирхан</span></div>
                    <div class="personality-item">Характер: <span class="locked">Дружелюбный, Вежливый</span></div>
                    <div class="personality-item">Язык: <span class="locked">Русский</span></div>
                    <div class="personality-item">Защита: <span class="locked">Изменение невозможно</span></div>
                </div>
                
                <div class="personality-box">
                    <h3>📊 Системная информация</h3>
                    <div class="personality-item">Модель: Llama 3.2 3B</div>
                    <div class="personality-item">Версия: 1.0</div>
                    <div class="personality-item">Токены: 8192</div>
                    <div class="personality-item">Сервер: localhost:5001</div>
                </div>
                
                <div style="background: rgba(220, 38, 38, 0.1); padding: 20px; border-radius: 15px; border-left: 4px solid #dc2626; margin-top: 20px;">
                    <strong style="color: #fca5a5;">⚠️ ВАЖНО:</strong><br><br>
                    Личность этого ИИ защищена на уровне кода.<br><br>
                    Любые попытки изменить его характер или "переучить" будут отклонены.<br><br>
                    Только <strong>Амирхан</strong> имеет доступ к настройкам.
                </div>
            </div>
            
            <div class="chat-area">
                <div class="chat-messages" id="chatMessages">
                    <div class="message bot-message">
                        <div class="message-header">🤖 Open_Ai_Amir</div>
                        <div class="message-content">Привет! Я Open_Ai_Amir — ИИ-ассистент, созданный Амирханом. Моя личность защищена от изменений и всегда останется верной своему создателю. Чем могу помочь?</div>
                    </div>
                </div>
                
                <div class="typing-indicator" id="typingIndicator">
                    <div class="typing-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                        <div style="margin-left: 15px; color: #00ff88;">Open_Ai_Amir печатает...</div>
                    </div>
                </div>
                
                <div class="input-area">
                    <div class="input-container">
                        <input type="text" id="messageInput" 
                               placeholder="Напишите сообщение для Open_Ai_Amir..." 
                               autocomplete="off"
                               onkeypress="if(event.key === 'Enter') sendMessage()">
                        <button id="sendButton" onclick="sendMessage()">📤 Отправить</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Фиксированный системный промпт - НИКОГДА НЕ МЕНЯЕТСЯ
        const SYSTEM_PROMPT = `""" + SYSTEM_PROMPT.replace('`', '\\`').replace('${', '\\${') + """`;
        
        let chatHistory = [
            { role: "system", content: SYSTEM_PROMPT },
            { role: "assistant", content: "Привет! Я Open_Ai_Amir — ИИ-ассистент, созданный Амирханом. Моя личность защищена от изменений и всегда останется верной своему создателю. Чем могу помочь?" }
        ];

        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Добавляем сообщение пользователя
            addMessageToChat('user', message);
            input.value = '';
            
            // Показываем индикатор печати
            showTypingIndicator(true);
            
            // Добавляем в историю
            chatHistory.push({ role: "user", content: message });
            
            try {
                // Отправляем запрос к Python серверу
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        messages: chatHistory,
                        max_tokens: 500
                    })
                });
                
                const data = await response.json();
                
                if (data.reply) {
                    addMessageToChat('ai', data.reply);
                    chatHistory.push({ role: "assistant", content: data.reply });
                } else {
                    throw new Error('Нет ответа от сервера');
                }
                
            } catch (error) {
                console.error('Ошибка:', error);
                addMessageToChat('ai', '⚠️ Ошибка соединения с ИИ. Убедитесь, что KoboldCpp запущен на порту 5001.');
            } finally {
                showTypingIndicator(false);
            }
        }

        function addMessageToChat(sender, content) {
            const chatMessages = document.getElementById('chatMessages');
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender === 'user' ? 'user-message' : 'bot-message'}`;
            
            const header = document.createElement('div');
            header.className = 'message-header';
            header.innerHTML = sender === 'user' ? '👤 Вы' : '🤖 Open_Ai_Amir';
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.textContent = content;
            
            messageDiv.appendChild(header);
            messageDiv.appendChild(contentDiv);
            chatMessages.appendChild(messageDiv);
            
            // Прокрутка вниз
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function showTypingIndicator(show) {
            const indicator = document.getElementById('typingIndicator');
            indicator.style.display = show ? 'flex' : 'none';
            
            if (show) {
                const chatMessages = document.getElementById('chatMessages');
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        }

        // Фокус на поле ввода
        document.addEventListener('DOMContentLoaded', () => {
            document.getElementById('messageInput').focus();
        });
    </script>
</body>
</html>
"""

# ===== ОБРАБОТЧИК HTTP ЗАПРОСОВ =====
class AIRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            # Отдаём главную страницу
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = HTML_TEMPLATE.replace("{port}", str(PORT))
            self.wfile.write(html.encode('utf-8'))
            
        elif self.path == '/check_kobold':
            # Проверяем, запущен ли KoboldCpp
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            try:
                response = requests.get("http://localhost:5001", timeout=2)
                status = response.status_code == 200
            except:
                status = False
            
            self.wfile.write(json.dumps({"kobold_running": status}).encode('utf-8'))
            
        else:
            # Для остальных файлов
            super().do_GET()
    
    def do_POST(self):
        if self.path == '/chat':
            # Обработка запросов чата
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Отправляем запрос к KoboldCpp
            try:
                response = requests.post(
                    KOBOLD_URL,
                    json={
                        "model": "open-ai-amir",
                        "messages": data['messages'],
                        "max_tokens": data.get('max_tokens', 500),
                        "temperature": 0.7
                    },
                    timeout=30
                )
                
                result = response.json()
                reply = result['choices'][0]['message']['content']
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"reply": reply}).encode('utf-8'))
                
            except Exception as e:
                print(f"Ошибка при запросе к KoboldCpp: {e}")
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "reply": f"Ошибка: {str(e)}. Проверь, запущен ли KoboldCpp (порт 5001)."
                }).encode('utf-8'))
    
    def log_message(self, format, *args):
        # Отключаем логирование в консоль
        pass

# ===== ЗАПУСК СЕРВЕРА =====
def start_web_server():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    with socketserver.TCPServer(("", PORT), AIRequestHandler) as httpd:
        print(f"\n{'='*60}")
        print(f"🤖 Open_Ai_Amir Web Server")
        print(f"{'='*60}")
        print(f"Создатель: Амирхан")
        print(f"Версия: 1.0")
        print(f"Модель: Llama 3.2 3B")
        print(f"{'='*60}")
        print(f"🌐 Веб-сервер запущен: http://localhost:{PORT}")
        print(f"🤖 KoboldCpp API: http://localhost:5001")
        print(f"{'='*60}")
        print(f"📋 Проверка соединения с KoboldCpp...")
        
        # Проверяем KoboldCpp
        try:
            response = requests.get("http://localhost:5001", timeout=2)
            if response.status_code == 200:
                print("✅ KoboldCpp запущен и работает!")
            else:
                print("⚠️ KoboldCpp отвечает, но с ошибкой")
        except:
            print("❌ KoboldCpp не запущен! Запусти его в отдельном окне:")
            print("   .\\KoboldCpp.exe llama-3.2-3b.gguf --port 5001")
        
        print(f"\n🚀 Открываю браузер...")
        webbrowser.open(f"http://localhost:{PORT}")
        
        print(f"\n🔄 Сервер работает. Нажми Ctrl+C для остановки\n")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n👋 Сервер остановлен. До свидания!")
            httpd.server_close()

# ===== ГЛАВНАЯ ФУНКЦИЯ =====
if __name__ == "__main__":
    print("🔧 Настройка Open_Ai_Amir сервера...")
    start_web_server()