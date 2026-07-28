import os

from typing import Optional, Dict, List

from openai import OpenAI

from hello_agent import HelloAgentsLLM

class MyLLM(HelloAgentsLLM):
    """docstring for MyLLM"""
    def __init__(self, 
                model : Optional[str] = None, 
                api_key : Optional[str] = None, 
                base_url : Optional[str] = None, 
                provider : Optional[str] = "auto",
                **kwargs):
              
        if provider == "modelscope":
            print ("正在使用自定义的 ModelScope Provider")
            
            self.provider = "modelscope"

            self.api_key = api_key or os.getenv("MODELSCOPE_API_KEY")

            self.base_url = base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"

            if not self.api_key:
                raise ValueError("ModelScope API key not found. Please set MODELSCOPE_API_KEY environment variable.")

            self.model = model or os.getenv("MODELSCOPE_MODEL_ID") or "qwen3-max"

            self.temperature = kwargs.get("temperature", 0.7)

            self.max_tokens = kwargs.get("max_tokens")

            self.time_out = kwargs.get("time_out")

            self.client = OpenAI(api_key = self.api_key, base_url = self.base_url, timeout=self.time_out)

        else:
            super().__init__(model, api_key, base_url, provider=provider, **kwargs)
