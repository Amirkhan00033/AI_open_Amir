@echo off
echo 🌐 Запускаю туннель для Open_Ai_Amir...
echo.

echo Вариант 1: Ngrok (если установлен)
ngrok tunnel 8888
echo.

echo Вариант 2: Cloudflared именованный туннель
cloudflared tunnel run open-ai-amir --url http://localhost:8888
echo.

echo Вариант 3: Локальная сеть
echo Твой IP: 
ipconfig | findstr IPv4
echo Друзья откроют: http://ТВОЙ_IP:8888
echo.
pause