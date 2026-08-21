from typing import Dict, List, Any, Optional, TYPE_CHECKING

from tool_base import Tool, ToolParameter

if TYPE_CHECKING:
    from mcp_tool import MCPTool
class MCPWrappedTool(Tool):
    """
    MCP工具包装器 - 将单个MCP工具包装成HelloAgents Tool

    这个类将MCP服务器的一个工具（如 read_file）包装成一个独立的 Tool 对象
    Agent 调用工具时候只需提供参数，无需了解内容实现
    """

    def __init__(
            self, 
            mcp_tool: "MCPTool",
            tool_info: Dict[str, Any], 
            prefix: str = ""):

        self.mcp_tool = mcp_tool
        self.tool_info = tool_info
        self.mcp_tool_name = tool_info.get('name', 'unknown')

        # 构建工具名：
        tool_name = f"{prefix}{self.mcp_tool_name}" if prefix else self.mcp_tool_name

        # 获取描述
        description = self.tool_info.get('description', f'MCP工具: {self.mcp_tool_name}')

        # 解析参数 schema
        self._parameters = self._parse_input_schema(tool_info.get('input_schema', {}))

        super().__init__(name = tool_name, description = description)

    def _parse_input_schema(self, input_schema: Dict[str, Any]):
        """
        将MCP的input_schema转换为HelloAgentsLLM 的ToolParameter列表
        """
        parameters = []

        properties = input_schema.get('properties', {})

        requires_fields = input_schema.get('required', [])

        for param_name, param_info in properties.items():
            param_type = param_info.get('type', 'string')
            param_desc = param_info.get('description', '')
            is_required = param_name in requires_fields

            parameters.append(ToolParameter(
                name = param_name,
                type = param_type,
                description = param_desc,
                required = is_required
            ))

        return parameters

    def get_parameters(self):
        """
        获取工具参数定义
        return ToolParameters列表
        """
        return self._parameters

    def run(self, params: Dict[str, Any]):
        """
        执行MCP工具

        Args：
           params: 工具参数（直接传递给MCP工具）
        
        Return
           执行结果
        """

        # 构建MCP调用参数
        mcp_params = {
            "action": "call_tool",
            "tool_name": self.tool_name,
            "arguments": params
        }

        # 调用MCP工具
        return self.mcp_tool.run(mcp_params)



