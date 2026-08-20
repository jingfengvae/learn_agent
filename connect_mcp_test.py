import asyncio
from mcp_client import MCPClient

async def connect_to_server():
    """
    方式：连接到自定义的Python MCP 服务器
    """
    client = MCPClient([
        "python", "mcp_server.py"
    ])

    # 使用 async with 确保连接正确关闭
    async with client:
        tools = await client.list_tools()
        print (f"可用工具：{[t['name'] for t in tools]}")

asyncio.run(connect_to_server())