from typing import List, Dict, Any, Optional
from learn_llm import HelloAgentsLLM

INITIAL_PROMPT_TEMPLATE = """
                    你是一位资深的Python程序员。请根据以下要求，编写一个Python函数。
                    你的代码必须包含完整的函数签名、文档字符串，并遵守PEP 8编码规范。

                    要求：{task}

                    请直接输出代码，不要包含任何额外的解释。
                          """


REFLECT_PROMPT_TEMPLATE = """
                    你是一位及其严格的代码评审专家和资深算法工程师，对代码的性能有极致的要求。
                    你的任务是审查一下Python代码，并专注于找出其在<strong>算法效率</strong>上的主要瓶颈。

                    # 原始任务：
                    {task}

                    待审查的代码：
                    ```python
                    {code}

                    请分析该代码的时间复杂度，并思考是否存在一种<strong>算法上更优</strong>的解决方案来显著提升性能。
                    如果存在，请清晰地指出当前算法的不足，并提出具体的、可行的改进算法建议（例如，使用筛法替代试除法）。
                    如果代码在算法层面已经达到最优，才能回答“无需改进”。
                    请直接输出你的反馈，不要包含任何额外的解释。
                          """

REFINE_PROMPT_TEMPLATE = """
                    你是一位资深的Python程序员。你正在根据一位代码评审专家的反馈来优化你的代码。

                    # 原始任务：
                    {task}

                    #你上一轮的代码：
                    ```
                    {last_code_attempt}

                    评审员的反馈：
                    {feedback}

                    请根据评审员的反馈，生成一个优化后的新版本代码。
                    你的代码必须包含完整的函数签名、文档字符串，并遵循PEP 8编码规范。
                    请直接输出优化后的代码，不要包含任何额外的解释。
                         """


class Memory:
    
    def __init__(self):
        """初始化一个空列表来存储所有记录 """
        self.records : List[Dict[str, Any]] = []

    def add_record(self, record_type, content):

        record = {"type": record_type, "content": content}

        self.records.append(record)

        print (f"记录更新， 新增一条'{record}'记录。")

    def get_trajectory(self):

        trajectory_parts = []

        for record in self.records:
            if record["type"] == "excution":
                trajectory_parts.append(f"--- 上一轮尝试（代码）---\n {record['content']}")
            elif record["type"] == "reflection":
                trajectory_parts.append(f"--- 评审员反馈 --- \n {record['content']}")

        return "\n\n".join(trajectory_parts)

    def get_last_execution(self):

        for record in reversed(self.records):
            if record["type"] == "excution":
                return record["content"]
        return None


class ReflectionAgent:

    def __init__(self, llm_client, max_iterations = 3):

        self.llm_client = llm_client

        self.memory = Memory()

        self.max_iterations = max_iterations


    def run(self, task):

        print (f"\n --- 开始处理 ---\n 任务: {task}")

        initial_prompt = INITIAL_PROMPT_TEMPLATE.format(task = task)

        initial_code = self.get_llm_response(initial_prompt)

        self.memory.add_record("excution", initial_code)

        for i in range(self.max_iterations):

            print (f"\n--- 第 {i + 1} / {self.max_iterations} 轮迭代 ---")

            last_code = self.memory.get_last_execution()

            reflect_prompt = REFLECT_PROMPT_TEMPLATE.format(task=task, code=last_code)

            feedback = self.get_llm_response(reflect_prompt)

            self.memory.add_record("reflection", feedback)

            if "无需改进" in feedback:
                print  (f"\n 反思认为代码已无需改进， 任务完成。")
                break

            print (f"\n ---> 正在进行优化...")

            refine_prompt = REFINE_PROMPT_TEMPLATE.format(task=task, last_code_attempt = last_code, feedback = feedback)

            refined_code = self.get_llm_response(refine_prompt)

            self.memory.add_record("excution", refined_code)

        final_code = self.memory.get_last_execution()

        print (f"\n 任务完成 ---\n 生成的最终的代码：\n ```Python: \n {final_code}\n```")

    def get_llm_response(self, prompt):

        messages = [{"role": "user", "content": prompt}]

        response_text = self.llm_client.think(message=messages) or ""

        return response_text


if __name__ == '__main__':

    model = "gpt-4o-mini"

    llmClient = HelloAgentsLLM(model)
    
    task = "编写一个Python函数，找出1到n之间所有的素数 (prime numbers)。"

    agent = ReflectionAgent(llmClient, 5)

    agent.run(task)      
