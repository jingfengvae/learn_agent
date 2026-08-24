"""
基于官方 a2a-sdk 库的 A2A 协议实现

使用官方 a2a-sdk 库实现 Agent-to-Agent Protocol 功能。
"""

from typing import Dict, List, Any, Optional

class A2AClient:
    """A2A 客户端 （通过HTTP 与 A2AServer 通信）"""

    def __init__(self, server_url: str):
        """
        初始化 A2A 客户端
        
        Args：
            server_url: 服务器url
        """
        self.server_url = server_url.rstrip("/")
    
    def ask(self, question: str):
        """
        向 Agent 提问 (通用接口)

        Args:
           question: 问题文本

        Returns:
           Agent 回答
        """

        try:
            import requests
            response = requests.post(f"{self.server_url}/ask", json = {"question": question}, timeout = 60)
            response.raise_for_status()
            return response.json().get("answer", "No Response")
        except Exception as e:
            print (f"Error: agent request : {str(e)}")
            return f"Error: request error: {e}"

    def execute_skill(self, skill_name: str, text: str = ""):
        """
        执行指定的技能

        Args:
            skill_name: 技能名称
            text: 输入文本
        
        Returns:
           执行结果
        """

        try:
            import requests
            response = requests.post(f"{self.server_url}/execute/{skill_name}", json = {'text': text}, timeout = 30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print (f"Error: failed to execute {skill_name}: {e}")
            return {
                "error": f"Error: Failed to execute skill: {str(e)}",
                "status": "error"
            }
    
    def get_info(self):
        """获取Agent信息"""
        try:
            import requests
            response = requests.get(f"{self.server_url}/info", timeout = 10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print (f"Failed to get agent info: {e}")
            return {
                "error": f"Failed to get agent info: {e}",
                "status": "error"
            }

    def list_skills(self):
        """列出Agent的所有技能"""
        try:
            import requests
            response = requests.get(f"{self.server_url}/skills", timeout = 10)
            response.raise_for_status()
            return response.json().get("skills", [])
        except Exception as e:
            print (f"Failed to get agent skills: {e}")
            return []

    

        
# 创建客户端
client = A2AClient("http://localhost:5000")

# 发送请求
response = client.execute_skill("research")
print (f"收到的响应: {response}")

