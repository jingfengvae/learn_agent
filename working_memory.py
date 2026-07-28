from memory_base import BaseMemory, MemoryItem, MemoryConfig
from typing import List, Dict, Any
from datetime import datetime, timedelta
import heapq

class WorkingMemory(BaseMemory):
    """工作记忆的具体实现"""
    def __init__(self, config: MemoryConfig, storage_backend=None):
        super().__init__(config, storage_backend)
        # 工作记忆特定配置
        self.max_capacity = self.config.working_memory_capacity
        self.max_tokens = self.config.working_memory_tokens
        # 纯内存TTL（分钟），可通过在 MemoryConfig 上挂载 working_memory_ttl_minutes 覆盖
        self.max_age_minutes = getattr(self.config, 'working_memory_ttl_minutes', 120)
        self.current_tokens = 0
        self.session_start = datetime.now()
        
        # 内存存储（工作记忆不需要持久化）
        self.memories: List[MemoryItem] = []
        
        # 使用优先级队列管理记忆
        self.memory_heap = []  # (priority, timestamp, memory_item)

    def add(self, memory_item: MemoryItem):
        """添加记忆"""

        # 过期清理
        self._expire_old_memories()

        # 计算优先级(重要性 + 时间衰减)
        priority = self._calculate_priority(memory_item)

        # 添加记忆到堆中
        heapq.heappush(self.memory_heap, (-priority, memory_item.timestamp, memory_item))
        self.memories.append(memory_item)

        # 更新当前token数量
        self.current_tokens += len(memory_item.content.split())
        
        # 检查是否超出容量
        self._enforce_capacity_limits()
        return memory_item.memory_id
    
    def retrieve(self, query:str, limit: int = 5, user_id: str = None, **kwargs):
        """检索工作记忆 - 混合语义向量检索 和 关键词匹配"""

        # 过期清理
        self._expire_old_memories()
        if not self.memories():
            return

        # 过滤已遗忘的记忆
        active_memories = [memory for memory in self.memories if not memory.metadata.get("forgotten", False)]

        # 按用户ID过滤
        filtered_memories = active_memories

        if user_id:
            filtered_memories = [memory for memory in filtered_memories if memory.user_id == user_id]

        if not filtered_memories:
            return []

        # 尝试语义向量检索（如果嵌入模型）
        vector_scores = {}
        try:
            # 简单的语义相似度计算
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy

            # 准备文档
            documents = [query] + [m.content for m in filtered_memories]

            # TF-IDF 向量化
            vectorizer = TfidfVectorizer(stop_words=None, lowercase=True)
            tfidf_matrix = vectorizer.fit_transform(documents)

            # 计算余弦相似度
            query_vector = tfidf_matrix[0:1]
            document_vectors = tfidf_matrix[1:]
            cosine_similarities = cosine_similarity(query_vector, document_vectors).flatten()

            # 存储向量分数
            for i, memory in enumerate(filtered_memories):
                vector_scores[memory.memory_id] = cosine_similarities[i]
        except Exception as e:
            # 如果嵌入模型不可用，忽略向量检索
            vector_scores = {}
        
        # 计算最终分数
        query_lower = query.lower()
        scored_memories = []
        for memory in filtered_memories:
            content_lower = memory.content.lower()

            # 获取向量分数
            vector_score = vector_scores.get(memory.memory_id, 0)

            # 关键词匹配分数
            keyword_score = 0.0
            if query_lower in content_lower:
                keyword_score = len(query_lower) / len(content_lower)
            else:
                # 计算关键词匹配的部分分数
                query_words = set(query_lower.split())
                content_words = set(content_lower.split())
                common_words = query_words.intersection(content_words)
                if common_words:
                    keyword_score = len(common_words) / len(content_words)

            # 混合分数 = 向量分数 + 关键词匹配分数
            if vector_score > 0:
                final_score = vector_score * 0.7 + keyword_score * 0.3
            else:
                final_score = keyword_score

            # 时间衰减
            time_decay = self._calculate_time_decay(memory.timestamp)
            base_relevance *= time_decay

            # 重要性权重
            importance_weight = memory.importance * 0.4 + 0.8
            final_score = importance_weight * base_relevance

            if final_score > 0:
                scored_memories.append((final_score, memory))

        # 按分数排序并返回前 limit 个记忆
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        return [memory for _, memory in scored_memories[:limit]]
    
    def update(self, memory_id: str, content: str = None,
               importance: float = None, metadata: Dict[str, Any] = None) -> bool:
        """更新记忆"""
        for memory in self.memories:
            if memory.id == memory_id:
                old_tokens = len(memory.content.split())
                if content is not None:
                    memory.content = content
                    new_tokens = len(content.split())
                    self.current_tokens = self.current_tokens - old_tokens + new_tokens
                if importance is not None:
                    memory.importance = importance
                if metadata is not None:
                    memory.metadata.update(metadata)
                return True
        return False

    def _expire_old_memories(self):
        """按照TTL清理过期记忆，并同步更新堆和token计数"""
        if not self.memories:
            return
        
        cutoff_time = datetime.now() - timedelta(minutes=self.max_age_minutes)
        
        #过滤保留的记忆
        kept: List[MemoryItem] = []
        removed_token_sum = 0
        for memory in self.memories:
            if memory.timestamp >= cutoff_time:
                kept.append(memory)
            else:
                removed_token_sum += len(memory.content.split())
        
        if len(kept) == len(self.memories):
            return
        # 覆盖列表与token计数
        self.memories = kept
        self.current_tokens = max(0, self.current_tokens - removed_token_sum)
        
        # 重建堆
        self.memory_heap = []

        for memory in self.memories:
            priority = self._calculate_priority(memory)
            heapq.heappush(self.memory_heap, (-priority, memory.timestamp, memory))

    def _calculate_priority(self, memory_item: MemoryItem) -> float:
        """计算记忆优先级"""
        # 基础优先级 = 重要性
        priority = memory_item.importance

        # 时间衰减
        time_decay = self._calculate_time_decay(memory_item.timestamp)
        priority *= time_decay          

        return priority

    def _calculate_time_decay(self, timestamp: datetime) -> float:
        """计算时间衰减"""
        time_diff = datetime.now() - timestamp
        time_diff_hours = time_diff.total_seconds() / 3600
        # 指数衰减，越久远越小
        decay_factor = self.config.time_decay_factor ** (time_diff_hours / 6) # 6小时衰减一半
        return max(0.1, decay_factor)

    def _enforce_capacity_limits(self):
        """强制执行容量限制"""

        # 检查记忆容量限制
        while len(self.memories) > self.max_capacity:
            self._remove_lowest_priority_memory()

        # 检查token容量限制
        while self.current_tokens > self.max_tokens:
            self._remove_lowest_priority_memory()

    def _remove_lowest_priority_memory(self):
        """移除优先级最低的记忆"""
        if not self.memory_heap:
            return
 
        # 找到优先级最低的记忆
        lowest_priority = float('inf')
        lowest_memory = None
        for memory in self.memories:
            priority = self._calculate_priority(memory)
            if priority < lowest_priority:
                lowest_priority = priority
                lowest_memory = memory
        
        if lowest_memory:
            self.remove(lowest_memory.id)

    def remove(self, memory_id: str) -> bool:
        """移除记忆"""
        for i, memory in enumerate(self.memories):
            if memory.id == memory_id:
                removed_memory = self.memories.pop(i)

                # 从堆中移除
                self._mark_deleted_in_heap(memory_id)
                
                # 更新token计数
                self.current_tokens -= len(removed_memory.content.split())
                self.current_tokens = max(0, self.current_tokens)
                return True 
        return False

    def _mark_deleted_in_heap(self, memory_id: str):
        """标记堆中记忆为已删除"""
        pass

    def get_memory(self, priority: int = 0) -> MemoryItem:
        """按索引获取记忆"""
        return self.memories[priority]

    def has_memory(self, memory_id: str) -> bool:
        """检查记忆是否存在"""
        return any(memory.id == memory_id for memory in self.memories)

    def clear(self):
        """清空所有工作记忆"""
        self.memories.clear()
        self.memory_heap.clear()
        self.current_tokens = 0

    def get_stats(self) -> Dict[str, Any]:
        """获取工作记忆统计信息"""
        # 过期清理（惰性）
        self._expire_old_memories()
        
        # 工作记忆中的记忆都是活跃的（已遗忘的记忆会被直接删除）
        active_memories = self.memories
        
        return {
            "count": len(active_memories),  # 活跃记忆数量
            "forgotten_count": 0,  # 工作记忆中已遗忘的记忆会被直接删除
            "total_count": len(self.memories),  # 总记忆数量
            "current_tokens": self.current_tokens,
            "max_capacity": self.max_capacity,
            "max_tokens": self.max_tokens,
            "max_age_minutes": self.max_age_minutes,
            "session_duration_minutes": (datetime.now() - self.session_start).total_seconds() / 60,
            "avg_importance": sum(m.importance for m in active_memories) / len(active_memories) if active_memories else 0.0,
            "capacity_usage": len(active_memories) / self.max_capacity if self.max_capacity > 0 else 0.0,
            "token_usage": self.current_tokens / self.max_tokens if self.max_tokens > 0 else 0.0,
            "memory_type": "working"
        }

    def get_recent(self, limit: int = 10) -> List[MemoryItem]:
        """获取最近的记忆"""
        sorted_memories = sorted(
            self.memories, 
            key=lambda x: x.timestamp, 
            reverse=True
        )
        return sorted_memories[:limit]
    
    def get_important(self, limit: int = 10) -> List[MemoryItem]:
        """获取重要记忆"""
        sorted_memories = sorted(
            self.memories,
            key=lambda x: x.importance,
            reverse=True
        )
        return sorted_memories[:limit]

    def get_all(self) -> List[MemoryItem]:
        """获取所有记忆"""
        return self.memories.copy()
    
    def get_context_summary(self, max_length: int = 500) -> str:
        """获取上下文摘要"""
        if not self.memories:
            return "No working memories available."
        
        # 按重要性和时间排序
        sorted_memories = sorted(
            self.memories,
            key=lambda m: (m.importance, m.timestamp),
            reverse=True
        )
        
        summary_parts = []
        current_length = 0
        
        for memory in sorted_memories:
            content = memory.content
            if current_length + len(content) <= max_length:
                summary_parts.append(content)
                current_length += len(content)
            else:
                # 截断最后一个记忆
                remaining = max_length - current_length
                if remaining > 50:  # 至少保留50个字符
                    summary_parts.append(content[:remaining] + "...")
                break
        
        return "Working Memory Context:\n" + "\n".join(summary_parts)
    
    def forget(self, strategy: str = "importance_based", threshold: float = 0.1, max_age_days: int = 1) -> int:
        """工作记忆遗忘机制"""
        forgotten_count = 0
        current_time = datetime.now()
        
        to_remove = []
        
        # 始终先执行TTL过期（分钟级）
        cutoff_ttl = current_time - timedelta(minutes=self.max_age_minutes)
        for memory in self.memories:
            if memory.timestamp < cutoff_ttl:
                to_remove.append(memory.id)
        
        if strategy == "importance_based":
            # 删除低重要性记忆
            for memory in self.memories:
                if memory.importance < threshold:
                    to_remove.append(memory.id)
        
        elif strategy == "time_based":
            # 删除过期记忆（工作记忆通常以小时计算）
            cutoff_time = current_time - timedelta(hours=max_age_days * 24)
            for memory in self.memories:
                if memory.timestamp < cutoff_time:
                    to_remove.append(memory.id)
        
        elif strategy == "capacity_based":
            # 删除超出容量的记忆
            if len(self.memories) > self.max_capacity:
                # 按优先级排序，删除最低的
                sorted_memories = sorted(
                    self.memories,
                    key=lambda m: self._calculate_priority(m)
                )
                excess_count = len(self.memories) - self.max_capacity
                for memory in sorted_memories[:excess_count]:
                    to_remove.append(memory.id)
        
        # 执行删除
        for memory_id in to_remove:
            if self.remove(memory_id):
                forgotten_count += 1
        
        return forgotten_count
