from dataclasses import dataclass

from typing import Optional, Dict, Any, List

from datetime import datetime

@dataclass
class ContextPacket(object):
    """docstring for ContextPacket"""
    """
    候选信息包
    """
    content: str

    timestamp: datetime

    token_count: int

    relevance_score: float = 0.5

    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """初始化后处理"""

        if self.metadata is None:
            self.metadata = {}

        # 确保相关性分数在有效范围内
        self.relevance_score = max(0.0, min(1.0, self.relevance_score))

@dataclass
class ContextConfig:
    """上下文构建配置"""

    max_tokens: int = 3000

    reserve_ratio: float = 0.2

    min_relevance: float = 0.1

    enable_compression: bool = True

    recency_weight: float = 0.3

    relevance_weight: float = 0.7

    def __post_init__(self):
        assert 0.0 <= self.reserve_ratio <= 1.0, "reserve_ratio 必须在[0, 1] 范围内"
        assert 0.0 <= self.min_relevance <= 1.0, "min_relevance 必须在[0, 1] 范围内"
        assert abs(self.recency_weight + self.relevance_weight - 1.0) < 1e-6, "recency_weight + relevance_weight 必须小于等于1.0" 

