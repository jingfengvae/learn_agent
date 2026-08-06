import os

from openai import OpenAI

from typing import Dict, List

class HelloAgentsLLM:
    """docstring for HelloAgentsLLM"""
    def __init__(self, model):

        self.model = model
    
        self.client = OpenAI(api_key="sk-7QVK3bnSGwlrKpfjNnnUTRnKxX2BEQRfruyEXpfExYCaQtk2s",  base_url="https://api.chatanywhere.tech")
    

    def think(self, message, temperature = 0):
        print (f"正在调用{self.model}模型")

        try:
            response = self.client.chat.completions.create(
                model = self.model,
                messages = message,
                temperature = temperature,
                stream = False
                )
            
            if not response.choices:
                print("❌ choices 为空！")
                return None

            print ("大模型响应成功：")
            """
            collected_content = []
            for chunk in response:
                if not chunk.choices:
                    continue
                content = chunk.choices[0].delta.content or ""
                print (content, end="", flush = True)
                collected_content.append(content)
            """
            print ()
            #return "".join(collected_content)
            return response.choices[0].message.content
        except Exception as e:
            print (f" X 调用 LLM API 时发生错误：{e}")
            return None


if __name__ == '__main__':
    
    model = "gpt-5.2"

    llmClient = HelloAgentsLLM(model)

    message = [{"role": "system", "content": "You are a helpful assistant that writes C++ Code"},
               {"role": "user", "content": "写一个快速排序算法"}]

    print ("-----调用LLM----")

    responseText = llmClient.think(message, temperature = 0)

    print (responseText)


