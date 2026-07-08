@echo off
chcp 65001 >nul
cd /d "d:\python练习\数字生命"
echo 正在启动数字生命...
echo Python路径: D:\python练习\coures_scraper\.venv\Scripts\python.exe
echo 脚本路径: 乐乐.py
echo.
"D:\python练习\coures_scraper\.venv\Scripts\python.exe" "乐乐.py"
if errorlevel 1 (
    echo.
    echo ========================================
    echo 启动失败！请检查以下问题：
    echo 1. 虚拟环境是否存在
    echo 2. PySide6是否已安装
    echo ========================================
    pause
)