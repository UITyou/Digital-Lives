@echo off
chcp 65001 >nul
cd /d "d:\python练习\数字生命"
echo 正在启动数字生命...
"D:\python练习\coures_scraper\.venv\Scripts\python.exe" "乐乐.py"
if errorlevel 1 (
    echo 启动失败，请检查错误信息
    pause
)