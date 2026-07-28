from hello_agent import HelloAgentsLLM
from memory_tool import MemoryTool
from simple_agent import SimpleAgent
from tool_registry import ToolRegistry
from dotenv import load_dotenv

load_dotenv()

llm = HelloAgentsLLM()

agent = SimpleAgent(name="记忆助手", llm = llm)

memory_tool = MemoryTool(user_id="user123")
tool_registry = ToolRegistry()
tool_registry.register_tool(memory_tool)
agent.tool_registry = tool_registry

print ("==== 添加记忆 ====")

# 添加第一个记忆
result1 = memory_tool.execute("add", content = "用户张三是一个Python开发工程师，专注于机器学习与数据分析", memory_type="semantic", importance=0.8)

print (f"记忆1: {result1}")
