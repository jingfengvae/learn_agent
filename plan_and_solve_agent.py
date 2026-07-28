from typing import Optional, List, Dict, Any
from agent_base import Agent
from hello_agent import HelloAgentsLLM

from config import Config
from message import Message
import ast

DEFAULT_PLANNER_PROMPT = """
            你是一个顶级的AI规划专家。你的任务是将用户提出的复杂问题分解成一个由多个简单步骤组成的行动计划。
            请确保计划中的每个步骤都是一个独立的、可执行的子任务，并且严格按照逻辑顺序执行。
            你的输出必须是一个Python列表，其中每一个元素都是一个子任务的字符串。

            问题: {question}

            请严格按照以下步骤输出你的计划:
            ```Python
            ["步骤一", "步骤二", "步骤三", ...]
            ```
            """

DEFAULT_EXECUTOR_PROMPT = """
            你是一个顶级的AI执行专家。你的任务是严格按照给定的计划，一步步解决问题。
            你将收到原始问题、完整的计划以及目前为止完成的步骤和结果。
            请你专注于解决“当前步骤”，并仅输出该步骤的最终答案，不要输出任何额外的解释或对话。

            # 原始问题:
            {question}

            # 完整计划:
            {plan}

            #历史步骤与结果:
            {history}

            # 当前步骤:
            {current_step}

            请仅输出针对“当前步骤”的回答:

            """

class Planer:

    def __init__(self, 
                llm: HelloAgentsLLM,
                prompt_template: Optional[str] = None):
        self.llm = llm
        self.prompt_template = prompt_template if prompt_template else DEFAULT_PLANNER_PROMPT

    def plan(self, question, **kwargs):

        prompt = self.prompt_template.format(question = question)

        messages = [{"role": "user", "content": prompt}]

        print ("------ 正在生成计划 ------\n")
        response = self.llm.invoke(messages, **kwargs)

        print (f"计划已生成: \n{response}")

        try:
            # 提取Python代码中的列表
            # plan_str = response.strip().split("```Python")[1].split("```")[0].strip()
            plan_str = response.strip()
            plan = ast.literal_eval(plan_str)
            return plan if isinstance(plan, list) else []
        except (ValueError, SyntaxError, IndexError) as e:
            print (f"解析计划时出错: {e}")
            print (f"原始响应: {response}")
            return []
        except Exception as e:
            print (f"解析计划时发生未知Error: {e}")
            return []

class Executor:

    def __init__(self, 
                llm: HelloAgentsLLM, 
                prompt_template: Optional[str] = None):

        self.llm = llm
        self.prompt_template = prompt_template if prompt_template else DEFAULT_EXECUTOR_PROMPT


    def execute(self, question, plan, **kwargs):
        
        history = ""
        final_answer = ""

        print ("\n --- 正在执行计划 ---\n")

        for i, step in enumerate(plan, 1):
            print (f"\n ---> 正在执行步骤 {i} / {len(plan)} : {step}\n")


            prompt = self.prompt_template.format(
                                        question = question, 
                                        plan = plan,
                                        history = history,
                                        current_step = step)

            messages = [{"role": "user", "content": prompt}]

            response = self.llm.invoke(messages, **kwargs)

            history += f"步骤{i}: {step}\n结果:{response}\n\n"

            final_answer = response

            print (f" 步骤{i} 已完成，结果: {final_answer}")

        return final_answer


class PlanAndSolveAgent(Agent):

    def __init__(self, 
                name, 
                llm, 
                system_prompt: Optional[str] = None, 
                config: Optional[Config] = None,
                custom_prompts: Optional[Dict[str, str]] = None):
        super().__init__(name, llm, system_prompt, config)

        if custom_prompts:
            plan_prompt = custom_prompts.get("planner")
            execute_prompt = custom_prompts.get("executor")
        else:
            plan_prompt = None
            execute_prompt = None

        self.planner = Planer(self.llm, plan_prompt)
        self.executor = Executor(self.llm, execute_prompt)

    def run(self, input_text, **kwargs):

        print (f"\n {self.name}开始处理问题: {input_text}\n")

        plan = self.planner.plan(input_text)

        if not plan:
            final_answer = "无法生成有效的行动计划，任务终止。"
            print (f"\n ----- 任务终止 ----\n{final_answer}")

            self.add_message(Message(input_text, "user"))
            self.add_message(Message(final_answer, "assistant"))

            return final_answer

        final_answer = self.executor.execute(input_text, plan)

        print (f"\n ---- 任务完成 -----\n 最终答案: {final_answer}")

        self.add_message(Message(input_text, "user"))
        self.add_message(Message(final_answer, "assistant"))

        return final_answer








