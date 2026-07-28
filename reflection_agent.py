from typing import Optional, List, Dict, Any
from agent_base import Agent
from hello_agent import HelloAgentsLLM
from config import Config
from message import Message

# 默认提示词

DEFAULT_PROMPTS = {
                "initial":
                """
                请根据以下要求完成任务: 
                任务: {task}

                请提供一个完整、准确的回答。
                """,

                "reflect":
                """
                请仔细审查以下回答，并找出肯呢个的问题或者改进空间:

                # 原始任务: 
                {task}

                # 当前回答:
                {content}

                请分析这个回答的质量，指出不足之处，并提出具体的改进建议。
                如果回答已经很好，请回答“无需改进”。
                """,

                "refine":
                """
                请根据反馈意见改进你的回答:

                # 原始任务
                {task}

                # 上一轮回答:
                {last_attempt}

                # 反馈意见:
                {feedback}

                请提供一个改进后的回答。
                """
                }

class Memory:

    def __init__(self):
        self.records: List[Dict[str, Any]] = []

    def add_record(self, record_type, content):
        self.records.append({"type": record_type, "content": content})
        print (f"记忆已更新，新增一条'{record_type}'记录")

    def get_trajectory(self):
        trajectory = ""
        for record in self.records:
            if record['type'] == "execution":
                trajectory += f"--- 上一轮尝试(代码): \n{record['content']}\n\n"
            elif record['type'] == "reflection":
                trajectory += f"--- 评审员反馈 ---\n{record['content']}\n\n"
        return trajectory.strip()

    def get_last_execution(self):
        for record in reversed(self.records):
            if record['type'] == "execution":
                return record['content']
        return ""



class ReflectionAgent(Agent):
    def __init__(
                self,
                name: str,
                llm: HelloAgentsLLM,
                system_prompt: Optional[str] = None,
                config: Optional[Config] = None,
                max_iterations: int = 3,
                custom_prompts: Optional[Dict[str, str]] = None):
        super().__init__(name, llm, system_prompt, config)
        self.max_iterations = max_iterations
        self.memory = Memory()

        # 设置提示词模版：用户自定义优先，否则使用默认模版
        self.prompts = custom_prompts if custom_prompts else DEFAULT_PROMPTS

    def run(self, input_text, **kwargs):
        print (f"\n {self.name} 开始任务处理: {input_text}\n")

        initial_prompt = self.prompts["initial"].format(task=input_text)

        initial_result = self._get_llm_response(initial_prompt, **kwargs)

        self.memory.add_record("execution", initial_result)

        for i in range(self.max_iterations):
            print (f"\n--- 第{i + 1} / {self.max_iterations} 轮迭代 ---")

            print ("\n --> 正在进行反思.....")

            last_result = self.memory.get_last_execution()

            reflect_prompt = self.prompts["reflect"].format(
                            task = input_text,
                            content = last_result)
            feedback = self._get_llm_response(reflect_prompt, **kwargs)

            self.memory.add_record("reflection", feedback)

            if "无需改进" in feedback or "no need for improvement" in feedback.lower():
                print ("\n 反思认为结果已无需改进，任务完成。")
                break

            print ("\n --> 正在进行优化。。。")

            refine_prompt = self.prompts["refine"].format(task = input_text, 
                                                last_attempt = last_result,
                                                feedback = feedback)

            refined_result = self._get_llm_response(reflect_prompt, **kwargs)
            self.memory.add_record("execution", refined_result)

        final_result = self.memory.get_last_execution()
        print (f"\n--- 任务完成 ---\n 最终结果:\n {final_result}")

        # 保存到历史记录
        self.add_message(Message(input_text, "user"))
        self.add_message(Message(final_result, "assistant"))

        return final_result

    def _get_llm_response(self, prompt, **kwargs):
        messages = [{"role": "user", "content": prompt}]
        return self.llm.invoke(messages, **kwargs) or ""
