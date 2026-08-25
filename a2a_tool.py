from typing import Dict, List, Any, Optional
from tool_base import Tool, ToolParameter
from a2a_client import A2AClient

class A2ATool(Tool):
    """
    A2A 工具

    连接到 A2A Agent 并进行通信

    功能：
       - 向Agent提问
       - 获取 Agent 信息
       - 发送自定义消息
    """

    def __init__(
            self, 
            agent_url: str,
            name: str, 
            description: str = None):

        """
        初始化 A2A 工具
        
        Args:
            - agent_url: Agent URL
            - name: 工具名称
            - description: 工具描述
        """

        if description is None:
            description = "连接到 A2A Agent, 支持提问和获取信息。"

        super().__init__(name = name, description = description)

        self.agent_url = agent_url

    def run(self, parameters: Dict[str, Any]):
        """
        执行 A2A 操作

        Args:
            parameters: 包含以下参数字典
                - action: 操作类型 （ask, get_info）
                - question: 问题文本 （ask 需要）
        
        Returns：
            操作结果
        """

        action = parameters.get('action', "").lower()

        if not action:
            return "Error: 必须指定action参数"

        try:
            client = A2AClient(self.agent_url)

            if action == "ask":
                question = parameters.get("question")

                if not question:
                    return "Error: 必须指定 question 参数"

                response = client.ask(question)
                return f"Agent 回答: {response}"
            elif action == "get_info":
                info = client.get_info()
                result = "Agent 信息：\n"
                for key, value in info.items():
                    result += f"- {key}: {value}"
                return result
            else:
                return f"Error: 不支持的操作 {action}"
        except Exception as e:
            print (f"A2A 操作失败: {e}")
            return f"A2A 操作失败: {e}"

    def get_parameters(self):
        """获取工具定义参数"""
        return [
            ToolParameter(
                name = "action",
                type = "str",
                description = "操作类型: ask(提问), get_info(获取信息)",
                required = True
            ),

            ToolParameter(
                name = "question",
                type = "string",
                description = "问题文本 (ask 操作需要)",
                required = False
            )
        ]

