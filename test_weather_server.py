"""
测试 天气查询 MCP 服务器
"""

import asyncio
import os, json
from mcp_client import MCPClient

async def test_weather_server():
    server_script = os.path.join(os.path.dirname(__file__), "mcp_weather_server.py")
    client = MCPClient(["python", server_script])

    try:
        async with client:
            # 测试1：获取服务器信息
            info = json.loads(await client.call_tool("get_server_info", {}))
            print (f"服务器信息: {info}")

            # 测试2：列出所有城市
            cities = json.loads(await client.call_tool("list_supported_cities", {}))
            print (f"所有城市信息: {cities}")
    except Exception as e:
        print (f"测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_weather_server())