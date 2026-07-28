import os
from dotenv import load_dotenv
from openai import OpenAI

from typing import Dict, List


load_dotenv()

class HelloAgentsLLM:
    """docstring for HelloAgentsLLM"""
    def __init__(self):

        self.model = os.getenv("LLM_MODEL_ID")

        api_key = os.getenv("LLM_API_KEY")

        base_url = os.getenv("LLM_BASE_URL")

        time_out = os.getenv("LLM_TIMEOUT", 60)

        if not all([self.model, api_key, base_url]):
            raise ValueERROR("模型ID, api_key, base_url 必须被提供或在.env文件中提供。")
    
        self.client = OpenAI(api_key=api_key,  base_url=base_url)
    

    def invoke(self, messages, temperature = 0):
        print (f"正在调用{self.model}模型")

        try:
            response = self.client.chat.completions.create(
                model = self.model,
                messages = messages,
                temperature = temperature,
                stream = True
                )
            
            print ("大模型响应成功：")

            collected_content = []
            for chunk in response:
                if not chunk.choices:
                    continue
                content = chunk.choices[0].delta.content or ""
                print (content, end="", flush = True)
                collected_content.append(content)
            print ()
            return "".join(collected_content)
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


