"""
在Agent中使用天气 MCP 服务器
"""

import os
from dotenv import load_dotenv
from hello_agent import HelloAgentsLLM
from simple_agent import SimpleAgent
from mcp_tool import MCPTool

load_dotenv()

def create_weather_assistant():
    """创建天气助手"""

    llm = HelloAgentsLLM()

    assisant = SimpleAgent(
        name = "天气助手",
        llm = llm,
        system_prompt = """
                        你是一个天气助手，可以查询城市的天气信息。
                        使用 get_weather 工具查询天气，支持中文城市名。
                        """
    )

    # 添加天气MCP工具
    server_script = os.path.join(os.path.dirname(__file__), 'mcp_weather_server.py')
    weather_mcp_tool = MCPTool(
        name = "MCP天气工具",
        server_command = ["python", server_script]
    ) 

    # assisant.add_tool(weather_mcp_tool)
    
    # 显示展开并注册 MCP 子工具
    expanded_tools = weather_mcp_tool.get_expanded_tools()
    if not expanded_tools: 
        raise RuntimeError("未发现天气MCP子工具，请检查服务脚本、依赖")

    for tool in expanded_tools:
        assisant.add_tool(tool)
    
    return assisant

def interactive():
    """交互模式"""
    assisant = create_weather_assistant()

    while True:
        user_input = input("\n你: ").strip()
        if user_input.lower() in ['exit', 'quit']:
            break
        response = assisant.run(user_input)
        print (f'---->天气信息:\n {response}')

def demo():
    """演示"""

    assistant = create_weather_assistant()

    print ("\n查询北京天气")

    response = assistant.run("北京天气怎么样？")
    
    print (f"北京天气信息: {response}")

if __name__ == "__main__":
    demo()

    interactive()