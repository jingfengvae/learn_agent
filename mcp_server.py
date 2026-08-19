"""
基于 fastmcp 库的 MCP服务器的实现

使用 fastmcp 库实现 Model Context Protocl 服务器功能

fastmcp 是一个快速创建 MCP 服务器的 python库
"""

from typing import Dict, List, Optional, Any, Callable

from fastmcp import FastMCP

class MCPServer:
    def __init__(
            self,
            name: str,
            description: Optional[str] = None):
        """
        初始化 MCP 服务器

        Args:
            name: 服务器名称
            description: 服务器描述
        """
        self.mcp = FastMCP(name = name)

        self.name = name

        self.description = description or f"{name} MCP Server"

    def add_tool(
            self,
            func: Callable,
            name: Optional[str] = None,
            description: Optional[str] = None):

        """
        添加工具到服务器

        Args:
            func: 工具函数
            name: 工具名称
            description: 工具描述
        """

        if name or description:
            self.mcp.tool(name = name, description = description)
        else:
            self.mcp.tool()(func)

    def add_resource(
            self,
            func: Callable,
            uri: Optional[str] = None,
            name: Optional[str] = None,
            description: Optional[str] = None):

        """
        添加资源到服务器

        Args:
            func: 资源处理函数
            uri: 资源URI
            name: 资源名称
            description: 资源描述
        """
        # 使用装饰器注册资源
        if uri:
            self.mcp.resource(uri)(func)
        else:
            self.mcp.resource()(func)

    def add_prompt(
            self,
            func: Callable,
            name: Optional[str] = None,
            description: Optional[str] = None):
        """
        添加提示词模版到服务器

        Args：
            func: 提示词生成函数
            name: 提示词名称
            description: 提示词描述（可选）
        """

        if name or description:
            self.mcp.prompt(name, description = description)(func)
        else:
            self.mcp.prompt()(func)

    def run(self, transport: str = "stdio", **kwargs):
        """
        运行服务器
        
        Args：
           transport: 传输方式 （"stdio", "http", "sse"）

           **kwargs: 传输特定的参数
               - host: HTTP 服务器主机（默认：127.0.0.1）
               - port: HTTP 服务器端口（默认：8000）
               - 其他 FastMCP.run 支持的参数
        """

        self.mcp.run(transport = transport, **kwargs)

    def get_info(self):

        """
        获取服务器信息
        """
        return {
            "name": self.name,
            "description": self.description,
            "protocol": "MCP"
        }
        

## 便捷的服务器构建器
class MCPServerBuilder:
    """MCP 服务器构建器，提供链式 API"""

    def __init__(
            self,
            name: str,
            description: Optional[str] = None):
        self.server = MCPServer(name, description)

    def with_tool(
            self,
            func: Callable,
            name: Optional[str] = None,
            description: Optional[str] = None):
        """添加工具"""
        self.server.add_tool(func, name, description)
        return self

    def with_resource(
            self, 
            func: Callable,
            uri: Optional[str] = None,
            name: Optional[str] = None,
            description: Optional[str] = None):
        """添加资源"""
        self.server.add_resource(func, uri, name, description)
        return self
    
    def with_prompt(
            self,
            func: Callable,
            name: Optional[str] = None,
            description: Optional[str] = None):
        """添加提示词"""
        self.server.add_prompt(func, name, description)
        return self

    def build(self):
        """构建服务器"""
        return self.server

    def run(self):
        """运行服务器"""
        self.server.run()


# 实例：创建一个简单的 MCP 服务器
def create_example_mcp_server():
    """创建一个示例MCP服务器"""

    server = MCPServer(
        name = "example-server",
        description = "一个简单的MCP服务器，有简易计算工具和问候工具"
    )

    # 添加一个简单的计算器工具
    def calculator(expression: str):
        """
        计算数学表达式

        Args:
            expression: 需要计算的表达式
        """
        try:
            allowed_chars = set("0123456789+-*/().")
            if not all(c in allowed_chars for c in expression):
                return f"Error: Invalid characters in expression: {expression}"
            result = eval(expression)
            return f"result: {result}"
        except Exception as e:
            print (f"表达式: {expression}, 计算Error: {e}")
            return f"Error: {str(e)}"

    server.add_tool(calculator, name = "calculator", description = "计算一个数学表达式")

    # 添加一个问候工具
    def greet(name: str):
        """
        生成一个问候语
        Args：
            name: 名字
        """

        return f"Hello, {name}! Welcome to the MCP Server example"

    server.add_tool(greet, name = "greet", description = "友好的问候")

    return server

if __name__ == "__main__":
    # 创建并运行一个示例服务器
    server = create_example_mcp_server()

    print (f"Start {server.name} ....")
    print (f"{server.description}")

    print (f"Protocol: MCP")
    print (f"Transport: stdio")
    print ()

    server.run()
    

        
        
    
