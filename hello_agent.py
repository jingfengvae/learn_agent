import os
from dotenv import load_dotenv
from openai import OpenAI

from typing import Dict, List


load_dotenv()

class HelloAgentsLLM:
    """docstring for HelloAgentsLLM"""
    def __init__(self, **kwargs):

        self.model = os.getenv("LLM_MODEL_ID")

        self.api_key = os.getenv("LLM_API_KEY")

        self.base_url = os.getenv("LLM_BASE_URL")

        self.time_out = os.getenv("LLM_TIMEOUT", 60)

        self.kwargs = kwargs

        # 自动检测provider或使用指定的provider
        self.provider = self.auto_detect_provider()

        # 根据provider设置默认的模型ID、api_key和base_url
        if self.provider == "openai":
            self.model = os.getenv("LLM_MODEL_ID")
            self.api_key = os.getenv("LLM_API_KEY")
            self.base_url = os.getenv("LLM_BASE_URL")
        elif self.provider == "deepseek":
            self.model = os.getenv("DEEPSEEK_MODEL_ID")
            self.api_key = os.getenv("DEEPSEEK_API_KEY")
            self.base_url = os.getenv("DEEPSEEK_BASE_URL")
        elif self.provider == "qwen":
            self.model = os.getenv("DASHSCOPE_MODEL_ID")
            self.api_key = os.getenv("DASHSCOPE_API_KEY")
            self.base_url = os.getenv("DASHSCOPE_BASE_URL")

        if not all([self.model, self.api_key, self.base_url]):
            raise ValueError("模型ID, api_key, base_url 必须被提供或在.env文件中提供。")
    
        self.client = self.create_client()

    def create_client(self):
        # 创建客户端
        return OpenAI(api_key=self.api_key, base_url=self.base_url)
    
    def auto_detect_provider(self):
        if os.getenv("LLM_API_KEY"):
            return "openai"
        if os.getenv("DEEPSEEK_API_KEY"):
            return "deepseek"
        if os.getenv("DASHSCOPE_API_KEY"):
            return "qwen"
        raise ValueError("无法自动检测提供者，请检查base_url或在.env文件中指定。")

    def invoke(self, messages, temperature = 0.7):
        print (f"正在调用{self.model}模型")

        try:
            print (f"--------> messages: {messages}")
            response = self.client.chat.completions.create(
                model = self.model,
                messages = messages,
                temperature = temperature
                )
            
            print ("大模型响应成功：")
            """
            collected_content = []
            for chunk in response:
                if not chunk.choices:
                    continue
                content = chunk.choices[0].delta.content or ""
                print (content, end="", flush = True)
                collected_content.append(content)
            print ()
            return "".join(collected_content)
            """
            return response.choices[0].message.content
        except Exception as e:
            print (f" X 调用 LLM API 时发生错误：{e}")
            return None 
            
    def think(self, messages, temperature = None):
        print (f"正在调用{self.model}模型")
        
        try:
            response = self.client.chat.completions.create(
                model = self.model,
                messages = messages,
                temperature = temperature,
                stream = True
                )
            
            print ("大模型响应成功：")

            for chunk in response:
                if not chunk.choices:
                    continue
                content = chunk.choices[0].delta.content or ""
                print (content, end="", flush = True)
                yield content
            print ()
        except Exception as e:
            print (f" X 调用 LLM API 时发生错误：{e}")

    def stream_invoke(self, messages, **kwargs):
        temperature = kwargs.get('temperature')
        yield from self.think(messages, temperature)


