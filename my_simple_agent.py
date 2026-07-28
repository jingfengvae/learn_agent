from typing import Optional, Iterator, Dict, List, Any

from simple_agent import SimpleAgent
from hello_agent import HelloAgentsLLM
from config import Config
from message import Message

import re

class MySimpleAgent(SimpleAgent):
    """docstring for MySimpleAgent"""
    def __init__(self, 
                name: str,
                llm: HelloAgentsLLM, 
                system_prompt: Optional[str] = None,
                config: Optional[Config] = None,
                tool_registry: Optional['ToolRegistry'] = None,
                enable_tool_calling: bool = True):
        super().__init__(name, llm, system_prompt, config)
        self.tool_registry = tool_registry
        self.enable_tool_calling = enable_tool_calling
        print (f"{name} 初始化完成，工具调用：{'启用' if self.enable_tool_calling else '禁用'}")
    

    def run(self, input_text, max_tool_iterations = 5, **kwargs):

        print (f"{self.name} 正在处理：{input_text}")

        messages = []

        enhanced_system_prompt = self._get_enhance_system_prompt()
        messages.append({"role": "system", "content": enhanced_system_prompt})

        for msg in self._history:
            messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": input_text})

        if not self.enable_tool_calling:
            response = self.llm.invoke(messages, **kwargs)
            self.add_message(Message(input_text, "user"))
            self.add_message(Message(response, "assistant"))
            print (f"{self.name} 响应完成")
            return response

        return self._run_with_tools(messages, input_text, max_tool_iterations, **kwargs)

    def _run_with_tools(self, messages: list, input_text: str, max_tool_iterations: int, **kwargs) -> str:
        """支持工具调用的运行逻辑"""
        current_iteration = 0
        final_response = ""

        while current_iteration < max_tool_iterations:
            # 调用LLM
            response = self.llm.invoke(messages, **kwargs)

            # 检查是否有工具调用
            tool_calls = self._parse_tool_call(response)

            if tool_calls:
                print(f"🔧 检测到 {len(tool_calls)} 个工具调用")
                # 执行所有工具调用并收集结果
                tool_results = []
                clean_response = response

                for call in tool_calls:
                    result = self._execute_tool_call(call['tool_name'], call['parameters'])
                    tool_results.append(result)
                    # 从响应中移除工具调用标记
                    clean_response = clean_response.replace(call['original'], "")

                # 构建包含工具结果的消息
                messages.append({"role": "assistant", "content": clean_response})

                # 添加工具结果
                tool_results_text = "\n\n".join(tool_results)
                messages.append({"role": "user", "content": f"工具执行结果：\n{tool_results_text}\n\n请基于这些结果给出完整的回答。"})

                current_iteration += 1
                continue

            # 没有工具调用，这是最终回答
            final_response = response
            break

        # 如果超过最大迭代次数，获取最后一次回答
        if current_iteration >= max_tool_iterations and not final_response:
            final_response = self.llm.invoke(messages, **kwargs)

        # 保存到历史记录
        self.add_message(Message(input_text, "user"))
        self.add_message(Message(final_response, "assistant"))
        print(f"✅ {self.name} 响应完成")

        return final_response
