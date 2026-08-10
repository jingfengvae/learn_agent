from dataclasses import dataclass, field

from typing import Optional, Dict, Any, List, Tuple

from datetime import datetime

from memory_tool import MemoryTool
from rag_tool import RAGTool
import tiktoken
import math
from message import Message
@dataclass
class ContextPacket(object):
    """docstring for ContextPacket"""
    """
    候选信息包
    """
    content: str

    timestamp: datetime = field(default_factory=datetime.now)

    token_count: int = 0

    relevance_score: float = 0.5

    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """初始化后处理"""

        if self.metadata is None:
            self.metadata = {}

        # 确保相关性分数在有效范围内
        self.relevance_score = max(0.0, min(1.0, self.relevance_score))

        # 自动计算token_count，如果未提供
        if self.token_count == 0:
            self.token_count = count_tokens(self.content)

@dataclass
class ContextConfig:
    """上下文构建配置"""

    max_tokens: int = 3000

    reserve_ratio: float = 0.2

    min_relevance: float = 0.1

    enable_compression: bool = True

    recency_weight: float = 0.3

    relevance_weight: float = 0.7

    def get_available_tokens(self) -> int:
        """计算可用的最大令牌数"""
        return int(self.max_tokens * (1 - self.reserve_ratio))

    def __post_init__(self):
        assert 0.0 <= self.reserve_ratio <= 1.0, "reserve_ratio 必须在[0, 1] 范围内"
        assert 0.0 <= self.min_relevance <= 1.0, "min_relevance 必须在[0, 1] 范围内"
        assert abs(self.recency_weight + self.relevance_weight - 1.0) < 1e-6, "recency_weight + relevance_weight 必须小于等于1.0" 

class ContextBuilder:
    """上下文构建器"""

    def __init__(self,
                memory_tool: Optional[MemoryTool] = None,
                rag_tool: Optional[RAGTool] = None,
                config: Optional[ContextConfig] = None):
        self.memory_tool = memory_tool
        self.rag_tool = rag_tool
        self.config = config or ContextConfig()
        self._encoding = tiktoken.get_encoding("cl100k_base")

    def add_packet(self, packet: ContextPacket):
        """添加候选信息包"""
        if packet.relevance_score >= self.config.min_relevance:
            self.context_packets.append(packet)
    
    def _gether(self, 
                user_query: str,
                conversation_history: Optional[List[Message]] = None,
                system_instructions: Optional[str] = None,
                additional_packets: Optional[List[ContextPacket]] = None) -> List[ContextPacket]:
        """收集候选信息包"""
        packets = []

        # P0: 系统指令（强约束）
        if system_instructions:
            packets.append(ContextPacket(
                content=system_instructions,
                metadata={"type": "instructions"},
            ))

        #P1: 从记忆中获取任务状态和关键结论
        if self.memory_tool:
            try:
                state_results = self.memory_tool.run({
                    "action": "search",
                    "query": user_query,
                    "min_importance": 0.7,
                    "limit": 5
                })
            
                if state_results and "未找到" not in state_results:
                    packets.append(ContextPacket(
                        content=state_results,
                        metadata={"type": "related_memory"},
                    ))
            except Exception as e:
                print (f"MemoryTool error: {e}")

        #P2: 从RAG工具中获取相关知识
        if self.rag_tool:
            try:
                rag_results = self.rag_tool.run({
                    "action": "search",
                    "query": user_query,
                    "limit": 5
                })
            
                if rag_results and "未找到" not in rag_results and "错误" not in rag_results:
                    packets.append(ContextPacket(
                        content=rag_results,
                        metadata={"type": "knowledge_base"},
                    ))
            except Exception as e:
                print (f"RAGTool error: {e}") 

        #P3: 从对话历史中获取相关信息
        if conversation_history:
            recent_history = conversation_history[-10:]  # 取最近10条对话
            history_msg = "\n".join([f"[{msg.role}] {msg.content}" for msg in recent_history])
            packets.append(ContextPacket(
                content=history_msg,
                metadata={"type": "history_text", "count": len(recent_history)},
            ))

        #P4: 添加额外包
        packets.extend(additional_packets or [])

        return packets
    
    def _select(self, packets: List[ContextPacket], user_query: str) -> List[ContextPacket]:
        """筛选和排序候选信息包"""
        # 1、计算相关性分数
        query_tokens = set(user_query.lower().split())
        for packet in packets:
            content_tokens = set(packet.content.lower().split())
            if len(query_tokens) > 0:
                overlap = len(query_tokens & content_tokens)
                packet.relevance_score = overlap / len(query_tokens)
            else:
                packet.relevance_score = 0.0

        # 2、计算新近性
        def recency_score(ts: datetime) -> float:
            delta = max((datetime.now() - ts).total_seconds(), 0)
            return math.exp(-delta / 3600)  # 以小时为单位的衰减
        
        # 3、计算复合分：0.7 * 相关性 + 0.3 * 新近性
        scored_packets: List[Tuple[float, ContextPacket]] = []
        for packet in packets:
            recency = recency_score(packet.timestamp)
            composite_score = packet.relevance_score * 0.7 + recency_score(packet.timestamp) * 0.3
            packet.relevance_score = composite_score
            scored_packets.append((composite_score, packet))

        # 4、系统指令单独拿出，固定纳入
        system_packets = [p for (_, p) in scored_packets if p.metadata.get("type") == "instructions"]
        remaining_packets = [p for (_, p) in sorted(scored_packets, key=lambda x: x[0], reverse=True) if p.metadata.get("type") != "instructions"]
        
        # 5、根据min_relevance过滤
        filtered_packets = [p for (_, p) in remaining_packets if p.relevance_score >= self.config.min_relevance]

        # 6、按预算填充
        availble_tokens = self.config.get_available_tokens()
        selected: List[ContextPacket] = []
        used_tokens = 0

        # 先放入系统指令
        for packet in system_packets:
            if used_tokens + packet.token_count <= availble_tokens:
                selected.append(packet)
                used_tokens += packet.token_count
        
        # 再按分数放入其他包
        for packet in remaining_packets:
            if used_tokens + packet.token_count <= availble_tokens:
                selected.append(packet)
                used_tokens += packet.token_count

        return selected
    
    def _structure(self, 
                   selected_packets: List[ContextPacket], 
                   user_query: str, 
                   system_instructions: Optional[str]) -> str:
        """组织结构化模版"""
        sections = []

        # [Role & Policies] - 系统指令
        p0_packets = [p for p in selected_packets if p.metadata.get("type") == "instructions"]
        if p0_packets:
            sections.append("[Role & Policies]\n" + "\n".join([p.content for p in p0_packets]))

        # [Task] - 当前任务
        sections.append(f"[Task]\n用户问题: {user_query}")

        # [State] - 任务状态
        p1_packets = [p for p in selected_packets if p.metadata.get("type") == "task_state"]
        if p1_packets:
            sections.append("[State]\n关键进展与未决问题:\n" + "\n".join([p.content for p in p1_packets]))

        # [Evidence] - 相关证据
        p2_packets = [p for p in selected_packets if p.metadata.get("type") in {"related_memory", "knowledge_base", "retrieval", "tool_result"}]
        if p2_packets:
            sections.append("[Evidence]\n事实与引用:" + "\n".join([p.content for p in p2_packets]))

        # [Context] - 对话历史
        p3_packets = [p for p in selected_packets if p.metadata.get("type") == "history_text"]
        if p3_packets:
            sections.append("[Context]\n对话历史与背景：\n" + "\n".join([p.content for p in p3_packets]))

        # [Output] - 输出要求
        output_section = """ [Output]\n请按照以下格式回答，确保准确性和完整性。
                        1、结论（简洁明确）
                        2、依据（列出支撑证据及来源）
                        3、风险与假设（如有）
                        4、下一步行动建议（如适用）
                        """
        sections.append(output_section)
        return "\n\n".join(sections)

    def _compress(self, context: str) -> str:
        """压缩与规范胡上下文"""
        if not self.config.enable_compression:
            return context

        # 计算当前令牌数
        current_tokens = count_tokens(context)
        available_tokens = self.config.get_available_tokens()

        if current_tokens <= available_tokens:
            return context

        # 如果超出限制，进行压缩
        print (f"当前令牌数 {current_tokens} 超过可用令牌数 {available_tokens}，进行截断压缩。")
        # 按段落截断，保留结构
        lines = context.split("\n")
        compressed_lines = []
        used_tokens = 0

        for line in lines:
            line_tokens = count_tokens(line)
            if used_tokens + line_tokens <= available_tokens:
                compressed_lines.append(line)
                used_tokens += line_tokens
        return "\n".join(compressed_lines)

    def build_context(self,
                    user_query: str,
                    conversation_history: Optional[List[Message]] = None,
                    system_instructions: Optional[str] = None,
                    additional_packets: Optional[List[ContextPacket]] = None) -> str:
        """构建上下文"""
        # 根据时间戳和相关性分数排序
        # 1、gether: 收集候选信息

        packets = self._gether(
                user_query = user_query,
                conversation_history = conversation_history,
                system_instructions = system_instructions,
                additional_packets = additional_packets
        )

        #2、 Select 筛选与排序
        selected_packets = self._select(packets, user_query)

        #3、Structure 组织结构化模版
        structured_context = self._structure(
                            selected_packets = selected_packets,
                            user_query = user_query,
                            system_instructions = system_instructions)
        #4、Compress 压缩
        final_context = self._compress(structured_context)

        return final_context
    
def count_tokens(text: str) -> int:
    """计算文本的令牌数"""
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception as e:
        print(f"Error occurred while encoding text: {e}")
        return len(text) // 4