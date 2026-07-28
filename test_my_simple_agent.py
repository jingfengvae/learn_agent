from dotenv import load_dotenv

from hello_agent import HelloAgentsLLM

from my_simple_agent import MySimpleAgent

from tool_registry import ToolRegistry

from calculator_tool import CalculatorTool

# 加载环境变量
load_dotenv()

llm = HelloAgentsLLM()

# 测试1：基础对话Agent
"""
print ("==== 测试1：基础对话Agent ====")

agent = MySimpleAgent(name="基础对话", 
                    llm = llm, 
                    system_prompt = "你是一个AI助手")

response = agent.run("你好，请你自我介绍一下！")
print (f"基础对话响应：\n{response}\n")
"""

# 测试2： 带工具的Agent

print ("==== 测试2：带工具的Agent ====")
tool_registry = ToolRegistry()
calculator = CalculatorTool("my_calculator", "你是一个简单的数学计算工具，支持基本运算(+,-,*,/)和sqrt函数")
tool_registry.registry_tool(calculator)

 # 注册计算器函数
tool_registry.register_function(
        name="my_calculator",
        description="你是一个简单的数学计算工具，支持基本运算(+,-,*,/)和sqrt函数",
        func=calculator.run
)

"""
agent = MySimpleAgent(name = "增强助手",
	                llm = llm,
	                system_prompt = "你是一个AI助手，可以使用工具帮助用户。",
	                tool_registry=tool_registry,
	                enable_tool_calling=True)
response = agent.run("请帮我计算: 15 * 8 * 2 + 32 - 20")
print (f"增强工具响应：\n{response}\n")
"""

# 测试3： 流式响应
agent = MySimpleAgent(name="基础对话", 
                    llm = llm, 
                    system_prompt = "你是一个AI助手")
"""
print ("=== 测试3： 流式响应 ===")
print ("流式响应：", end="")

for chunk in agent.stream_run("请解释什么是人工智能？"):
    pass

"""
# 测试4： 动态添加工具

print ("\n ==== 测试4： 动态添加工具 ====")

print (f"添加工具前：{agent.has_tools()}")
agent.add_tool(calculator)
print (f"添加工具后：{agent.has_tools()}")
print (f"可用工具：{agent.list_tools()}")
# 查看历史对话
print (f"\n对话历史：{len(agent.get_history())}")



