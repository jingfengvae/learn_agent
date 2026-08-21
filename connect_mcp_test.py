import asyncio
from mcp_client import MCPClient
from mcp_tool import MCPTool
from hello_agent import HelloAgentsLLM
from simple_agent import SimpleAgent

# 1、MCP 工具访问
mcp_tool = MCPTool()
result = mcp_tool.run({
    "action": "call_tool",
    "tool_name": "add",
    "arguments":{"a": 10, "b":10}
})
print (f"MCP工具计算结果: {result}")

# 列出github_tool可用工具
print ("可用工具：")
result = mcp_tool.run({"action": "list_tools"})
print (result)

# 列出资源
print ("可用资源：")
result = mcp_tool.run({"action": "list_resources"})
print (result)

# 获取系统信息
result = mcp_tool.run(
    {
        "action": "call_tool",
        "tool_name": "get_system_info"
    }
    )
print (result)

# 在agent中使用MCP工具
agent = SimpleAgent(name = "AI 助手", llm = HelloAgentsLLM())
agent.add_tool(mcp_tool)
response = agent.run("计算 123 + 456")
print (response)
