from dotenv import load_dotenv

from hello_agent import HelloAgentsLLM

from reflection_agent import ReflectionAgent

load_dotenv()
llm = HelloAgentsLLM()

code_prompts = {
    "initial": "你是Python专家，请编写函数: {task}",
    "reflect": "请审查代码的算法效率: \n 任务: {task} \n代码: {content}",
    "refine": "请根据反馈优化代码: \n 任务: {task} \n 反馈: {feedback}"
}


agent = ReflectionAgent(name = "我的AI代码生成助手", 
                       llm = llm,
                       custom_prompts = code_prompts)

# 测试使用
question = "编写一个C++函数，找出1到n之间所有的素数 (prime numbers)。"
result = agent.run(question)



