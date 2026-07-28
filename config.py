import os

from dotenv import load_dotenv

from typing import Optional, Dict, List, Literal, Any

from pydantic import BaseModel

load_dotenv()

class Config(BaseModel):
    """HelloAgents配置类"""
    
    """LLM 配置"""
    default_model : str = "gpt-3.5-turbo"

    default_provider : str = "openai"

    temperature : float = 0.7

    max_tokens: Optional[int] = None
    
    """系统配置"""
    debug : bool = False

    log_level: str = "INFO"
    
    """其他配置"""
    max_history_length : int = 100

    @staticmethod
    def from_env(cls):
        return cls(
            debug = os.getenv("DEBUG", "false").lower() == "true",
            log_level = os.getenv("LOG_LEVEL", "INFO"),
            temperature = float(os.getenv("temperature", 0.7)),
            max_tokens = int(os.getenv("MAX_TOKENS")) if os.getenv("MAX_TOKENS") else None)

    def to_dict(self):
        return self.dict()
