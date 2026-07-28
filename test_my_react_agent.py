import os
from typing import Optional, Iterator, TYPE_CHECKING, Callable
from hello_agent import HelloAgentsLLM
from my_react_agent import MyReactAgent
from tool_registry import ToolRegistry
from calculator_tool import CalculatorTool
from search_tool import SearchTool
from dotenv import load_dotenv
# 加载环境变量
load_dotenv()

def test_react_agent():
    # 创建LLM
    llm = HelloAgentsLLM()
    
    # 创建工具表
    tool_registry = ToolRegistry()

    # 注册一些基础工具
    print ("注册测试工具。。。")
    
    #注册计算器工具
    try:
        calculator = CalculatorTool("my_calculator", "你是一个简单的数学计算工具，支持基本运算(+,-,*,/)和sqrt函数")
        tool_registry.registry_tool(calculator)
        tool_registry.register_function("calculator", "执行数学计算，支持基本的四则运算", calculator.run)
        print("✅ 计算器工具注册成功")
    except ImportError as e:
        print (f"计算器工具未找到，跳过注册: {e}")
    
    # 2、测试搜索工具
    #注册计算器工具
    try:
        searchtor = SearchTool("my_search", "你是一个高级搜索工具")
        tool_registry.registry_tool(searchtor)
        tool_registry.register_function("search", "高级搜索工具，整合Tavily和SerpAPI多个搜索源，提供更全面的搜索结果", searchtor.run)
        print("✅ 搜索工具注册成功")
    except ImportError as e:
        print (f"搜索工具未找到，跳过注册: {e}")

    
    agent = MyReactAgent(name = "我的AI助手",
                        llm = llm,
                        tool_registry = tool_registry,
                        max_steps=5)

    # 1、测试数学问题
    question = "请计算：(25 + 25) * 4 - 30 + 20"

    try:
        response = agent.run(question)
        print (f"计算结果是: {response}")
    except Exception as e:
        raise e
        print (f"测试失败：{e}")
    
    print ("------=====================-------")

    search_question = "我想去北京旅游。请为我推荐3个著名景点。"
    try:
        response = agent.run(search_question)
        print (f"搜索结果是: {response}")
    except Exception as e:
        raise e
        print (f"测试失败：{e}")

    print ("------=====================-------")
    # 3、测试复杂的问题
    print ("✅ 测试3：复合问题测试===")

    complex_question = "如果一个班级有100个学生，其中60%是女生，那么男生有多少人？请先计算女生人数，再计算男生人数。"
    try:
        response = agent.run(complex_question)
        print (f"搜索结果是: {response}")
    except Exception as e:
        raise e
        print (f"测试失败：{e}")



if __name__ == '__main__':
    test_react_agent()


     






