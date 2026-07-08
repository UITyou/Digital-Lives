import subprocess
import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

python_path = r"D:\python练习\coures_scraper\.venv\Scripts\python.exe"
script_path = os.path.join(script_dir, "乐乐.py")

print(f"正在启动数字生命...")
print(f"Python路径: {python_path}")
print(f"脚本路径: {script_path}")

result = subprocess.run([python_path, script_path], capture_output=True, text=True)

if result.returncode != 0:
    print(f"启动失败:")
    print(f"标准输出: {result.stdout}")
    print(f"错误输出: {result.stderr}")
    input("按回车键退出...")