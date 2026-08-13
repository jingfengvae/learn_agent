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

    terminal = TerminalTool(workspace=str(SCRIPT_DIR))

    # 第一步查看当前目录
    print (f"1、查看当前目录")
    result = terminal.run({"command": "ls -la"})
    print (result)

    print ("===" * 80)
    # 第二步：查看Python文件
    print (f"2、查看Python文件")
    result = terminal.run({"command": "ls -la *.py"})
    print (result)

    print ("===" * 80)
    # 第三步：查找特定的文件
    print (f"3、查找特定的文件")
    result = terminal.run({"command": "find . -name '*tool.py'"})
    print (result)

    print ("===" * 80)
    # 第四步：查看文件内容
    print (f"4、查看文件内容")
    result = terminal.run({"command": "cat terminal_tool.py"})
    print (result)

    print ("===" * 80)
    # 第五步：查看文件的前几行
    print("5. 查看文件前5行:")
    result = terminal.run({"command": "head -n 15 terminal_tool.py"})
    print(result)
    
    print ("===" * 80)
    # 第六步：统计总行数
    print("6. 统计文件行数:")
    result = terminal.run({"command": "wc -l terminal_tool.py"})
    print(result)



def main():
    demo_exploratory_navigation()

if __name__ == "__main__":
    main()