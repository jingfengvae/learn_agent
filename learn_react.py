import os
import re
from learn_tool import ToolExecutor, search
from learn_llm import HelloAgentsLLM

REACT_PROMPT_TEMPLATE = """
                        请注意，你是一个有能力调用外部工具的智能助手。
                        可用工具如下:
                        {tools}

                        请严格按照以下格式进行回应:

                        Thought:你的思考过程，用于分析问题、拆解任务和规划下一步行动。
                        Action:你决定采取的行动，必须是以下格式之一:
                        - `{{tool_name}} [{{tool_input}}]`:调用一个可用工具。
                        - `Finish[最终答案]`:当你认为已经获得最终答案时。
                        - 当你收集到足够的信息，能够回答用户的最终问题时，你必须在`Action:`字段后使用`Finish(answer="...")`来说输出最终答案。

                        现在，请开始解决以下问题：
                        Question:{question}
                        History:{history}
                        """

class ReActAgent:
    def __init__(self, llm_client, tool_executor, max_steps):
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.max_steps = max_steps
        self.history = []

    def run(self, question):
        self.history = []

        current_step = 0

        while current_step < self.max_steps:
            current_step += 1

            print (f"--- 第 {current_step} 步 ---")

            # 1、格式化提示词

            tool_desc = self.tool_executor.getAvailableTools()

            history_str = "\n".join(self.history)

            prompt = REACT_PROMPT_TEMPLATE.format(
                tools = tool_desc,
                question = question,
                history = history_str)

            # 2、调用 LLM 进行思考

            messages = [{"role": "user", "content": prompt}]

            response_text = self.llm_client.think(message = messages) 
            
            #print ("response_text:", response_text)

            if not response_text:
                print ("错误：LLM未能返回正确响应")
                break

            thought, action = self.parse_output(response_text)

            if thought:
                print (f"思考：{thought}")

            if not action:
                print (f"警告：未能解析出有效的Action， 流程终止。")
                break

            if action.startswith("Finish"):
                match = re.match(r"Finish\s*\[(.*)\]", action, re.DOTALL)
                
                if not match:
                    match = re.search(r'Finish\s*\(\s*answer\s*=\s*"(.*)"\s*\)', action, re.DOTALL)
                
                finial_answer = match.group(1) 

                print (f"最终答案：{finial_answer}")
                return finial_answer

            tool_name, tool_input = self.parse_action(action)

            if not tool_name or not tool_input:
                continue

            print (f"行动：{tool_name}[{tool_input}]")

            tool_function = self.tool_executor.getTool(tool_name)

            if not tool_function:
                observation = f"错误：未能找到名：'{tool_name}'的工具。"
            else:
                observation = tool_function(tool_input)

            print (f"观察：{observation}")

            self.history.append(f"Action：{action}")
            self.history.append(f"Observation：{observation}")

        print ("已达到最大步数，流程终止")
        return None

    def parse_output(self, text):

        """解析出LLM的输出， 提取Thought 和 Action"""

        thought_match = re.search(r"Thought[:：]\s*(.*?)(?=\nAction[:：]|$)", text, re.DOTALL)
        action_match = re.search(r"Action[:：]\s*(.*?)$", text, re.DOTALL)

        thought = thought_match.group(1).strip() if thought_match else None

        action = action_match.group(1).strip() if action_match else None

        return thought, action

    def parse_action(self, action_text):

        match = re.match(r"(\w+)\s*\[(.*)\]", action_text, re.DOTALL)

        if match:
            return match.group(1).strip(), match.group(2).strip()
        return None , None


if __name__ == '__main__':
    
    toolExecutor = ToolExecutor()

    search_decription = "一个网页搜索引擎，当你需要回答关于时事、事实以及在你的知识库找不到信息时，应使用此工具。"

    toolExecutor.registerTool("Search", search_decription, search)
    
    model = "gpt-4o-mini"

    llmClient = HelloAgentsLLM(model)

    reActAgent = ReActAgent(llmClient, toolExecutor, max_steps = 5) 

    question = "华为最新的手机是哪一款？它的主要卖点是什么？"

    reActAgent.run(question)