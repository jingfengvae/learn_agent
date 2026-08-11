from dotenv import load_dotenv
from typing import List, Any
from datetime import datetime
load_dotenv()
from hello_agent import HelloAgentsLLM
from simple_agent import SimpleAgent
from message import Message
from memory_tool import MemoryTool
from rag_tool import RAGTool
from context import ContextBuilder, ContextConfig

class ContextAwareAgent(SimpleAgent):
    """上下文感知的智能体，支持记忆和RAG功能"""
    
    def __init__(self, name: str, llm: HelloAgentsLLM, **kwargs):
        super().__init__(name, llm)
        self.memory_tool = MemoryTool(user_id = "user_123")
        self.rag_tool = RAGTool(knowledge_base_path="./knowledge_base")
        self.config = ContextConfig(max_tokens=1000, reserve_ratio=0.2, min_relevance=0, enable_compression=True)
        self.context_builder = ContextBuilder(self.memory_tool, self.rag_tool, config = self.config)
        self.conversation_history: List[Message] = []

    def run(self, user_input: str) -> str:
        # 运行智能体，自动构建优化上下文并调用LLM或RAG工具
        # 1、使用 ContextBuilder 构建优化上下文
        
        optimized_context = self.context_builder.build_context(user_query=user_input,
                                                     conversation_history=self.conversation_history,
                                                     system_instructions=self.system_prompt)

        # 2、使用优化后的上下文调用 LLM
        message = [
                    {"role": "system", "content": optimized_context},
                    {"role": "user", "content": user_input}
                ]
        response = self.llm.invoke(message)

        # 3、将用户输入和模型响应存储到会话历史中
        self.conversation_history.append(Message(content=user_input, role="user", timestamp=datetime.now()))
        self.conversation_history.append(Message(content=response, role="assistant", timestamp=datetime.now()))
        
        
        # 4、存储到记忆中
        self.memory_tool.run({
                    "action": "add",
                    "content": f"Q: {user_input} \n\n Answer: {response}",
                    "memory_type": "episodic",
                    "importance": 0.6
                })
        
        return response

def main():
    print ("ContextBuilder 与 Agent 集成实例")
    llm = HelloAgentsLLM()
    agent = ContextAwareAgent(name="数据分析顾问", llm=llm, system_prompt="你是一个资深数据分析顾问，擅长使用Python进行数据分析和可视化。")
    
    user_input = "如何支持处理实时数据流，你有什么建议吗？"
    response = agent.run(user_input)
    print(f"智能体回答: {response}")

if __name__ == "__main__":
    print ("=== ContextAwareAgent 测试 ===")
    print ("===" * 80)
    main()
    print ("===" * 80)