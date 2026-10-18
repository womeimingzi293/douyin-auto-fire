@echo off
cd /d "%~dp0\web"
echo 正在启动抖音自动续火花管理后台...
echo 浏览器将自动打开 http://127.0.0.1:5000
start http://127.0.0.1:5000
python app.py
pause
