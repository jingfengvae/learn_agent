from context import ContextBuilder, ContextConfig
from memory_tool import MemoryTool
from rag_tool import RAGTool
from message import Message
from datetime import datetime, timedelta
from hello_agent import HelloAgentsLLM

# 1、初始化工具
print ("1、初始化工具")
memory_tool = MemoryTool(user_id = "user_123")
rag_tool = RAGTool(knowledge_base_path="./knowledge_base")

# 2、创建ContextBuilder实例
print ("2、创建ContextBuilder实例")
config = ContextConfig(max_tokens=1000, reserve_ratio=0.2, min_relevance=0, enable_compression=True)
context_builder = ContextBuilder(config=config, memory_tool=memory_tool, rag_tool=rag_tool)

# 3、准备历史对话
print ("3、准备历史对话")
history_messages = [
    Message(content = "我正在开发一个数据分析工具", role = "user", timestamp = datetime.now() - timedelta(seconds=10)),
    Message(content = "听起来很有趣！数据分析工具通常需要处理大量数据，你希望这个工具具备哪些功能？您计划使用什么技术栈？", role = "assistant", timestamp = datetime.now() + timedelta(seconds=5)),
    Message(content = "我希望它能够处理大数据集，并提供可视化分析功能。我计划使用Python和相关的数据分析库，如Pandas和Matplotlib，而且已经完成了CSV读取模块", role = "user", timestamp = datetime.now() + timedelta(seconds=10)),
    Message(content = "听起来你已经有了一个很好的起点。Pandas在数据处理方面非常强大。使用Python和Pandas进行数据处理是一个不错的选择，而Matplotlib可以帮助你创建各种可视化图表。你是否考虑过使用其他可视化库，如Seaborn或Plotly，以增强你的分析工具的功能？", role = "assistant", timestamp = datetime.now() + timedelta(seconds=15))
]

# 4、添加一些记忆
print ("4、添加一些记忆")
memory_tool.run({
            "action": "add",
            "content": "用户正在用Python开发数据分析工具，并且熟悉使用Pandas和Matplotlib库。",
            "memory_type": "semantic",
            "importance": 0.8
            })

memory_tool.run({
            "action": "add",
            "content": "已经完成CSV读取模块的开发",
            "memory_type": "episodic",
            "importance": 0.7
            })

# 5、构建上下文
print ("5、构建上下文")
final_context = context_builder.build_context(
                                    user_query="我想让这个工具支持实时数据流处理，你有什么建议吗？", 
                                    conversation_history=history_messages,
                                    system_instructions="你是一个Python数据分析工具开发的专家，提供关于实时数据流处理的建议。你的回答需要:1) 提供具体可行的建议 2) 解释技术原理 3) 给出代码示例")

print ("===" * 80)
print ("构建的上下文(结构化字符串): \n")
print ("===" * 80)
print (final_context)
print ("===" * 80)
print ()

# 6、将上下文字符串转化为消息格式提供给 LLM 使用
print ("6、将上下文字符串转化为消息格式提供给 LLM 使用")

message = [{"role": "system", "content": final_context},
           {"role": "user", "content": "请回答"}]

llm = HelloAgentsLLM()
response = llm.invoke(message)
print (f"LLM 回答：{response}")
print("✅ ContextBuilder 演示完成!")
print("\n提示: ContextBuilder 返回的是结构化的上下文字符串,")
print("可以直接作为 system message 传给 LLM。")




