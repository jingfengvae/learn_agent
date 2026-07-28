from dotenv import load_dotenv

from hello_agent import HelloAgentsLLM
from plan_and_solve_agent import PlanAndSolveAgent

load_dotenv()

llm = HelloAgentsLLM()

agent = PlanAndSolveAgent(name = "我的规划执行助手",
                    llm = llm)

#question = "一个水果店周一卖出了15个苹果。周二卖出的苹果数量是周一的两倍。周三卖出的数量比周二少了5个。请问这三天总共卖出了多少个苹果？"

question = "有若干只鸡和兔子，它们共有88个头，244只脚，鸡和兔各有多少只？"

response = agent.run(question)

print (f"最终结果: {response}")

print (f"对话历史: {len(agent.get_history())} 条消息")

