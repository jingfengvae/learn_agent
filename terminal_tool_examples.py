"""
测试使用 TerminalTool 
"""

from terminal_tool import TerminalTool
from pathlib import Path
import os

# 获取脚本所在的目录
SCRIPT_DIR= Path(__file__).parent.absolute()

def demo_exploratory_navigation():
    """演示探索式导航"""
    print ("===" * 80)

    termianl = TerminalTool(workspace=str(SCRIPT_DIR))

    # 第一步查看当前目录
    print (f"1、查看当前目录")
    result = termianl.run({"command": "ls -la"})
    print (result)

    print ("===" * 80)
    # 第二步：查看Python文件
    print (f"2、查看Python文件")
    result = termianl.run({"command": "ls -la *.py"})
    print (result)

    print ("===" * 80)
    # 第三步：查找特定的文件
    print (f"3、查找特定的文件")
    result = termianl.run({"command": "find . -name '*tool.py'"})
    print (result)

    print ("===" * 80)
    # 第四步：查看文件内容
    print (f"4、查看文件内容")
    result = termianl.run({"command": "cat terminal_tool.py"})
    print (result)



def main():
    demo_exploratory_navigation()

if __name__ == "__main__":
    main()