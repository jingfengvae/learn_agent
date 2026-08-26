"""
在智能体中使用 A2A 工具

简易智能客户系统
"""

from hello_agent import HelloAgentsLLM
from simple_agent import SimpleAgent
from a2a_server import A2AServer
from a2a_tool import A2ATool
from dotenv import load_dotenv
import threading
import time

load_dotenv()
llm = HelloAgentsLLM()

# 1、创建技术专家Agent服务

tech_expert = A2AServer(
    name = "tech_expert",
    description = "技术专家，回答技术问题"
)

@tech_expert.skill("answer")
def answer_tech_question(text: str):
    import re
    match = re.search(r'answer\s+(.+)', text, re.IGNORECASE)
    question = match.group(1).strip() if match else text

    # 实际应用中这里会调用LLM或者知识库
    # 现在这里只做简易回答
    return f"技术回答：关于'{question}', 我建议您看我们的技术文档...."

# 2、创建销售顾问Agent
sales_advisor = A2AServer(
    name = "sales_advisor",
    description = "销售顾问，回答销售问题"
)

@sales_advisor.skill("answer")
def answer_sales_advisor(text: str):
    import re
    match = re.search(r'answer\s+(.+)', text, re.IGNORECASE)
    question = match.group(1).strip() if match else text
    return f"销售回答: 关于'{question}', 我们有特别优惠..."

# 3、启动服务
threading.Thread(target=lambda: tech_expert.run(port = 6000), daemon = True).start()
threading.Thread(target=lambda: sales_advisor.run(port = 6001), daemon = True).start()
time.sleep(3)


# 4、创建接待员Agent (使用SimpleAgent)
receptionist = SimpleAgent(
    name = "接待员",
    llm = llm,
    system_prompt = """
                你是客服接待员，负责：
                1、分析客户的问题类型(技术问题 或 销售问题);
                2、将问题转发给相应的专家;
                3、整理专家的回答并返回给用户;

                可用工具：
                    - tech_expert: 回答技术问题
                    - sales_advisor: 回答销售问题  

                请保持专业和礼貌。
                """
)

# 添加技术专家工具
tech_tool = A2ATool(
                agent_url = "http://localhost:6000",
                name = "tech_expert",
                description = "技术专家，回答技术相关问题")
receptionist.add_tool(tech_tool)

# 添加销售顾问工具
sale_tool = A2ATool(
                agent_url = "http://localhost:6001",
                name = "sales_advisor",
                description = "销售顾问，回答价格、购买相关问题"
            )
receptionist.add_tool(sale_tool)

# 处理客户咨询
def handle_customer_query(query):
    print (f"\n客户咨询: {query}")
    print (f"==" * 50)
    response = receptionist.run(query)
    print (f"\n客服回答: {response}")
    print (f"==" * 50)

if __name__ == "__main__":
    handle_customer_query("你们的API如何调用？")
    handle_customer_query("企业版的价格是多少？")
    handle_customer_query("如何集成到我的项目中？")

