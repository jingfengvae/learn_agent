import asyncio
from mcp_client import MCPClient

async def connect_to_server():
    """
    方式1：连接到社区提供的文件系统服务器
    npx 会自动下载并运行@modelcontextprotocol/server-filesystem包
    """
    client = MCPClient([
        "npx", "-y", "@modelcontextprotocol/server-filesystem", "."
    ])

    # 使用 async with 确保连接正确关闭
    async with client:
        tools = await client.list_tools()
        print (f"可用工具：{[t['name'] for t in tools]}")

asyncio.run(connect_to_server())