import asyncio
from mcp_client import MCPClient
from mcp_tool import MCPTool

# 1、MCP 工具访问
mcp_tool = MCPTool()
result = mcp_tool.run({
    "action": "call_tool",
    "tool_name": "add",
    "arguments":{"a": 10, "b":10}
})
print (f"MCP工具计算结果: result = {result}")

