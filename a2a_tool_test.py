"""
在智能体中使用A2A工具
使用 A2ATool 包装器
"""
from hello_agent import HelloAgentsLLM
from simple_agent import SimpleAgent
from a2a_tool import A2ATool
from dotenv import load_dotenv
from a2a_server import A2AServer
import threading
import time


load_dotenv()

llm = HelloAgentsLLM()

# 假设已经有一个研究员Agent服务运行在 http://localhost:5000
#  创建 Agent 服务

# 创建一个协调者
coorinator = SimpleAgent(name="协调者", llm=llm)

# 添加A2A工具，连接到研究员Agent
research_tool = A2ATool(agent_url = "http://localhost:5000", name = "researcher", description="研究员Agent，可以搜索和分析资料")
coorinator.add_tool(research_tool)

# 协调者可以调用研究员Agent
response = coorinator.run("使用A2A工具, 工具中的参数action=ask, 向Agent提问: 请研究AI在教育领域的应用")
print (response)
