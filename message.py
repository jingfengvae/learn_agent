from typing import Optional, Dict, List, Literal, Any

from datetime import datetime

from pydantic import BaseModel

# 定义消息的角色类型， 限制其取值

messageRole = Literal["user", "assistant", "system", "tool"]

class Message(BaseModel):

    """消息类"""

    content : str

    role : messageRole

    timestamp: datetime = None

    metadata: Optional[Dict[str, Any]] = None

    def __init__(self, content, role, **kwargs):

        super().__init__(
                    content = content,
                    role = role,
                    timestamp = kwargs.get("timestamp", datetime.now()),
                    metadata = kwargs.get("metadata", {}))

    def to_dict(self):
        return {"role": self.role, "content": self.content}

    def __str__(self):
        return f"[{self.role}] {self.content}"

