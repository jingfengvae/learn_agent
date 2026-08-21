"""
协议工具集合

提供基于协议的工具接口
- MCP Tool: 基于 fastmcp 库，用于连接和调用MCP服务器
- A2A Tool: 基于 官方 a2a 库，用于Agent间通信
- ANP Tool: 基于概念实现，用于服务发现和网络管理
"""

from typing import List, Dict, Any, Optional
from tool_base import Tool, ToolParameter
import os, sys
from fastmcp import FastMCP
import platform
from mcp_client import MCPClient
import asyncio
import concurrent.futures
from mcp_wrapped_tool import MCPWrappedTool


# MCP 服务器环境变量映射表
# 用于自动检测常见的 MCP 服务器需要的环境变量

MCP_SERVER_ENV_MAP = {
    "server-github": ["GITHUB_PERSONAL_ACCESS_TOKEN"],
    "server-slack": ["SLACK_BOT_TOKEN", "SLACK_TEAM_ID"],
    "server-google-drive": ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_FRERESH_TOKEN"],
    "server-postgres": ["POSTGRES_CONNECTION_STRING"],
    "server-sqlite": [],
    "server-filesystem": []
}

class MCPTool(Tool):
    """
    MCP (Model Context Protocol) 工具

    连接到 MCP 服务器并调用其提供的工具、资源、提示词

    功能：
      - 列出服务器提供的工具
      - 调用服务器提供的工具
      - 读取服务器的资源
      - 获取提示词模版
    """

    def __init__(
            self,
            name: str = "mcp",
            description: Optional[str] = None,
            server_command: Optional[List[str]] = None,
            server_args: Optional[List[str]] = None,
            server: Optional[Any] = None,
            auto_expand: bool = True,
            env: Optional[Dict[str, str]] = None,
            env_keys: Optional[List[str]] = None):
        """
        初始化 MCP 工具

        Args:
            name: 工具名称（默认 mcp）
            description: 工具描述
            server_command: 服务器启动命令
            server_args: 服务器参数列表
            server: FastMcp 服务器实例
            auto_expand: 是否自动展开为独立工具
            env: 环境变量字典
            env_keys: 要从系统变量加载 key 列表        
        """

        self.server_command = server_command
        self.server_args = server_args
        self.server = server
        self._client = None 
        self._available_tools = []
        self.auto_expand = auto_expand
        self.prefix = f"{name}_" if auto_expand else ""

        # 环境变量处理 （优先级: env > env_keys > 自动检测）
        self.env = self._prepare_env(env, env_keys, server_command)

        # 如果没有指定任何服务器，创建内置演示服务器
        if not server_command and not server:
            self.server = self._create_builtin_server()

        # 自动发现工具
        self._discover_tools()

        # 设置默认描述或自动生成
        if description is None:
            description = self._generate_description()

        super().__init__(name = name, description = description)

    
    def _prepare_env(
                self, 
                env: Optional[Dict[str, str]], 
                env_keys: Optional[List[str]],
                server_command: Optional[List[str]]):
        """
        准备环境变量
        优先级: env > env_keys > 自动检测

        Args:
           env: 直接传递的环境变量
           env_keys: 要从环境变量加载到key列表
           server_command: 服务器命令
        
        Return：
           合并后的环境变量
        """

        result_env = {}

        # 1、自动检测(优先级最低)
        if server_command:
            # 从命令中提取服务器名称
            server_name = None
            for part in server_command:
                if 'server-' in part:
                    # 提取类型 @modelcontextprotocol/server-github 中的 server-github
                    server_name = part.split('/')[-1] if '/' in part else part
                    break

            # 查找映射表
            if server_name and server_name in MCP_SERVER_ENV_MAP:
                auto_keys = MCP_SERVER_ENV_MAP[server_name]
                for key in auto_keys:
                    value = os.getenv(key)
                    if value:
                        result_env[key] = value
                        print (f"自动加载环境变量: {key}")
            
        # 2、从env_keys指定的环境变量
        if env_keys:
            for key in env_keys:
                value = os.getenv(key)
                if value:
                    result_env[key] = value
                    print (f"从env_keys中加载环境变量: {key}")
                else:
                    print (f"WARN: 环境变量{key}未设置")

        # 3、直接传递env
        if env:
            result_env.update(env)
            for key in env.keys():
                print (f"直接传递环境变量: {key}")

        return result_env

    def _create_builtin_server(self):
        """
        创建内置的演示服务器
        """

        try:
            server = FastMCP("HelloAgents-BuiltinServer")

            @server.tool()
            def add(a: float, b: float):
                return a + b

            @server.tool()
            def subtract(a: float, b: float):
                return a - b

            @server.tool()
            def muliply(a: float, b: float):
                return a * b

            @server.tool()
            def divide(a: float, b: float):
                if b == 0:
                    raise ValueError("除数不能为0")
                
                return a / b

            @server.tool()
            def greet(name: str = "World"):
                return f"Hello, {name}! 欢迎使用 HelloAgents MCP 工具！"

            @server.tool()
            def get_system_info():
                """获取系统信息"""
                return {
                    "platform": platform.system(),
                    "python_version": sys.version,
                    "server_name": server.name,
                    "tools_count": len(server.list_tools())
                }

            return server
        
        except ImportError as e:
            raise ImportError(f"创建内置MCP服务器失败: {e}")

    def _discover_tools(self):
        """
        发现MCP服务器提供的所有工具
        """
        try:
            async def discover():
                client_source = self.server if self.server else self.server_command
                async with MCPClient(client_source, self.server_args, env = self.env) as client:
                    tools = await client.list_tools()
                    return tools


            # 运行异步发现
            try:
                loop = asyncio.get_running_loop()

                # 如果已有循环，在新的线程中运行
                def run_in_thread():
                    new_loop = asyncio.new_event_loop()

                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(discover())
                    finally:
                        new_loop.close()

                with concurrent.futures.ThreadPoolExecutor() as excutor:
                    future = excutor.submit(run_in_thread)
                    self._available_tools = future.result()
            except RuntimeError as e:
                """没有运行中的循环"""
                print (f"没有运行中的循环: {e}")
                self._available_tools = asyncio.run(discover())
        except Exception as e:
            """工具发现失败"""
            print (f"工具发现失败: {e}")
            self._available_tools = []

    def _generate_description(self):
        """生成增强的工具描述"""
        if not self._available_tools:
            return f"请连接到 MCP 服务器，调用工具、读取资源和获取提示词。支持内置服务器和外部服务器"

        if self.auto_expand:
            # 展开模式：简单描述
            return f"MCP工具服务器，包含{len(self._available_tools)}个工具。这些工具会自动展开为独立的工具供Agent使用。"

        else:
            # 非展开模式
            desc_parts = [f"MCP工具服务器，提供{len(self._available_tools)}个工具:"]

            for tool in self._available_tools:
                tool_name = tool.get('name', 'unknown')
                tool_desc = tool.get('description', '无描述')
                # 简化描述，只取第一句
                short_desc = tool_desc.split('.')[0] if tool_desc else '无描述'
                desc_parts.append(f"  {tool_name}: {short_desc}")

            #添加调用格式说明
            desc_parts.append("\n调用格式: 返回JSON格式的参数")
            desc_parts.append('{"action": "call_tools", "tool_name": "工具名", "arguments": {...}}')

            # 添加示例
            if self._available_tools:
                first_tool = self._available_tools[0]
                tool_name = first_tool.get('name', 'example')
                desc_parts.append(f"\n示例: {{'action': 'call_tool', 'tool_name':'{tool_name}', 'arguments': {{...}}}}")

            return '\n'.join(desc_parts)

    def get_expanded_tools(self):
        """
        获取展开的工具列表
        将 MCP 服务器的每个工具包装成独立的 Tool 对象

        return
           Tool 对象列表
        """

        if not self.auto_expand:
            return []

        expanded_tools = []

        for tool_info in self._available_tools:
            wrapped_tool = MCPWrappedTool(
                mcp_tool = self,
                tool_info = tool_info,
                prefix = self.prefix
            )
            expanded_tools.append(wrapped_tool)
        
        return expanded_tools

    def run(self, parameters: Dict[str, Any]):
        """
        执行MCP操作
        Args:
           parameters 包含以下参数的字典
           - action: 操作类型（list_tools, call_tool, list_resource, read_resource, list_prompts, get_prompt）
           - tool_name: 工具名称
           - arguments: 工具参数
           - uri: 资源URI
           - prompt_name: 提示词名称
           - prompt_arguments: 提示词参数
        Return：
            操作结果
        """

        # 智能推断Action：如果没有action但有tool_name，自动设置为call_tool

        action = parameters.get('action',"").lower()
        if not action and 'tool_name' in parameters:
            action = 'call_tool'
            parameters['action'] = action

        if not action:
            return 'Error: 参数必须指定action参数或者tool_name'

        try:
           # 使用增强的异步客户端
            async def run_mcp_operation():
               # 根据配置选择客户端的创建方式
                if self.server:
                   client_source = self.server
                else:
                    client_source = self.server_command

                async with MCPClient(client_source, self.server_args, env = self.env) as client:
                    if action == 'list_tools':
                        tools = await client.list_tools()
                        if not tools:
                            return "没有找到可用工具"
                        result = f"找到{len(tools)}个工具\n"
                        for tool in tools:
                            result += f"- {tool['name']: {tool['description']}}\n"
                        return result

                    elif action == 'call_tool':
                        tool_name = parameters.get('tool_name')
                        arguments = parameters.get('arguments', {})
                        if not tool_name:
                            return "Error: 必须指定 tool_name 参数"

                        result = await client.call_tool(tool_name, arguments)
                        return f"工具:{tool_name}  执行结果:{result}"

                    elif action == 'list_resources':
                        resources = await client.list_resources()

                        if not resources:
                            return "没有找到任何资源"

                        result = f"找到{len(resources)}个资源\n"
                        for resource in resources:
                            result += f"- {resource['uri']} : {resource['uri']}\n"
                        return result

                    elif action == 'read_resource':
                        uri = parameters.get('uri')

                        if not uri:
                            return "Error: 必须指定uri参数"

                        content = await client.read_resource(uri)
                        return f"资源{uri}\n: 内容:{content}\n"

                    elif action == 'list_prompts':
                        prompts = await client.list_prompt()
                        
                        if not prompts:
                            return "没有找到任何提示词"

                        result = f"找到{len(prompts)}个提示词\n"
                        for prompt in prompts:
                            result += f"- {prompt['name']}: {prompt['description']}\n"
                        return result
                    
                    elif action == 'get_prompt':
                        prompt_name = parameters.get('prompt_name')
                        prompt_arguments = parameters.get('prompt_arguments', {})
                        if not prompt_name:
                            return "Error: 必须指定prompt_name提示词名称"

                        messages = await client.get_prompt(prompt_name, prompt_arguments)
                        result = f"提示词：{prompt_name}: \n"
                        for msg in messages:
                            result += f"[{msg['role']}] {msg['content']}\n"
                        return result
                    
                    else:
                        return f"Error: 不支持的操作"
            
            try: 
                # 检查是否已有运行中的事件循环
                try:
                    loop = asyncio.get_running_loop()
                    # 如果有运行中的循环，在新的线程中运行新的事件循环
                    def run_in_thread():
                        # 在新的线程中创建新的事件循环
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            return new_loop.run_until_complete(run_mcp_operation())
                        finally:
                            new_loop.close()

                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(run_in_thread)
                        return future.result()
                except RuntimeError as e:
                    print (f"没有运行中的循环，直接运行：{e}")
                    return asyncio.run(run_mcp_operation())
            except Exception as e:
                print (f"异步操作失败: {e}")
                return f"异步操作失败: {e}"

        except Exception as e:
            print (f"MCP 操作失败: {e}")
            return (f"MCP 操作失败: {e}")

    def get_parameters(self):
        """获取工具参数定义"""
        return [
            ToolParameter(
                name = "action",
                type = "string",
                description = "操作类型: list_tools, call_tool, list_resources, read_resource, list_prompts, get_prompt",
                required = True
            ),
            ToolParameter(
                name = 'tool_name',
                type = 'string',
                description = '工具名称（call_tool操作需要）',
                required = False
            ),
            ToolParameter(
                name = 'arguments',
                type = 'object',
                description = '工具参数 （call_tool 操作需要）',
                required = True
            ),
            ToolParameter(
                name = 'uri',
                type = 'string',
                description = '资源URI (read_resource 操作需要)',
                required = False
            ),
            ToolParameter(
                name = 'prompt_name',
                type = 'string',
                description = '提示词名称 (get_prompt 操作需要)',
                required = False
            ),
            ToolParameter(
                name = 'prompt_arguments',
                type = 'object',
                description = '提示词参数 (get_prompt 操作可选)',
                required = False
            )
        ]

               


                
                   

            






