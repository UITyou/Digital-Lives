import sys
import traceback
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

try:
    exec(open('蚂蚁.py', encoding='utf-8').read())
except Exception as e:
    with open('error.log', 'w', encoding='utf-8') as f:
        f.write(f"错误类型: {type(e).__name__}\n")
        f.write(f"错误信息: {str(e)}\n")
        f.write("\n堆栈跟踪:\n")
        traceback.print_exc(file=f)
    print(f"错误: {type(e).__name__}: {str(e)}")