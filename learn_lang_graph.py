import os

import asyncio
from typing import TypedDict, Annotated
from typing import Dict, List
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from tavily import TavilyClient

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

class SearchState(TypedDict):

    messages : Annotated[List, add_messages]
    user_query : str  # 经过LLM理解后的用户需求总结
    search_query : str  # 优化后的用于 Tavily API 的搜索查询
    search_results : str  # Tavily 搜索返回的结果
    final_answer : str  # 最终生成的答案
    step : str         # 标记当前步骤


llm = ChatOpenAI(
    model = "gpt-4o-mini",
    api_key = "sk-cGxiB1iFm5gm3maLT1LHeFA2XguPZiU2GQ9rMs3wt8pbftcK",
    base_url = "https://api.chatanywhere.tech",
    temperature = 0.7
    )

api_key = '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'
tavily = TavilyClient(api_key = api_key)

def understand_query_node(state: SearchState):
    """
    步骤1：理解用户查询并生成搜索关键词
    """
    # 获取用户的最新查询信息
    user_message = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            user_message = msg.content
            break 
    
    understand_prompt = f"""
                分析用户的查询: "{user_message}"
                请完成两个任务:
                1、简洁总结用户想要了解什么;
                2、生成最适合搜索引擎的关键词（中英文均可，要精准）
                        
                格式: [用户需求总结]
                搜索词: [最佳搜索关键
                """
    
    response = llm.invoke([SystemMessage(content=understand_prompt)])
    response_text = response.content

    # 解析出LLM的输出，提取搜索关键词
    search_query = user_message
    if "搜索词:" in response_text:
        search_query = response_text.split("搜索词:")[-1].strip()

    return {
            "user_query": response_text,
            "search_query": search_query,
            "step": "understood",
            "messages": [AIMessage(content=f"我将为您搜索: {search_query}")] 
        }

def tavily_search_node(state: SearchState):
    """
    步骤2、使用Tavily API 进行搜索
    """
    search_query = state["search_query"]
    try:
        print (f"---> 正在搜索: {search_query}")
        response = tavily.search(query = search_query, search_depth = "basic", 
                                   max_results = 5, include_answer = True)
        # .... (处理和格式化搜索结果) ...
        search_results = ""
        if response.get('answer'):
            search_results = f"综合答案：{response['answer']}"
        
        if response.get("results"):
            search_results += "相关信息：\n"
            for i, result in enumerate(response["results"][:3], 1):
                title = result.get("title", "")
                content = result.get("content", "")
                url = result.get("url", "")
                search_results += f"{i}. {title}\n{content}\n来源: {url}\n\n" 

        if not search_results:
            search_results = "抱歉，没有找到相关信息。"

        return {
            "search_results": search_results,
            "step": "searched",
            "messages": [AIMessage(content="搜索完成，正在整理结果。。。")]   
            }
        
    except Exception as e:
        print (f"搜索出现问题：{e}")
        return {
                "search_results": f"搜索失败：{e}",
                "step": "search_failed",
                "messages": [AIMessage(content=f"搜索出现问题: {e}")]   
            }

def generate_answer_node(state: SearchState):
    """
    步骤3: 基于搜索结果生成最终答案
    """
    if state["step"] == "search_failed":
        fall_back_prompt = f"""
                        搜索API暂时不可用，请基于您的知识回答用户的问题: \n
                        用户问题: {state["user_query"]}
                        """
        response = llm.invoke([SystemMessage(content=fall_back_prompt)])
    else:
        answer_prompt = f"""
                        基于以下搜索结果为用户提供完整、准确的答案:
                        用户问题: {state["user_query"]} \n
                        搜索结果: \n {state["search_results"]}
                        请综合搜索结果，提供准确、有用的回答...
                        """
        response = llm.invoke([SystemMessage(content=answer_prompt)])

    return {
           "final_answer" : response.content,
           "step": "completed",
           "messages": [AIMessage(content=response.content)]
        }


def create_search_assistant():
    workflow = StateGraph(SearchState)

    # 添加节点
    workflow.add_node("understand", understand_query_node)
    workflow.add_node("search", tavily_search_node)
    workflow.add_node("answer", generate_answer_node)

    # 设置线性流程
    workflow.add_edge(START, "understand")
    workflow.add_edge("understand", "search")
    workflow.add_edge("search", "answer")
    workflow.add_edge("answer", END)

    # 编译图
    memory = InMemorySaver()
    app = workflow.compile(checkpointer=memory)
    return app


async def main():
    """
    主函数：运行智能搜索助手
    """

    app = create_search_assistant()

    print ("智能搜索助手启动！")
    print ("我会使用Tavily API 为您搜索最准确和最新的信息！")
    print ("输入（quit、q、exit）退出！")

    session_count = 0

    while True:
        user_input = input("您最想了解什么：").strip()

        if user_input.lower() in ["quit", "q", "exit"]:
            print ("感谢使用，再见！！")
            break

        session_count += 1

        config = {"configurable": {"thread_id": f"search-session-{session_count}"}}

        # 初始状态
        initial_state = {
            "messages" : [HumanMessage(content=user_input)],
            "user_query": "",
            "search_results": "",
            "search_query": "",
            "final_answer":"",
            "step":"start"
        }
        
        try:
            print ("\n ========================== ")

            # 执行工作流

            async for output in app.astream(initial_state, config = config):
                for node_name, node_output in output.items():
                    if "messages" in node_output and node_output["messages"]:
                        latest_message = node_output["messages"][-1]
                        if isinstance(latest_message, AIMessage):
                            if node_name == "understand":
                                print (f"\n理解阶段：{latest_message.content}")
                            elif node_name == "search":
                                print (f"\n搜索阶段：{latest_message.content}")
                            elif node_name == "answer":
                                print (f"\n最终答案：{latest_message.content}")

            print ("\n ========================== ")
        except Exception as e:
            print (f"发生错误:{e}")
            print ("请重新输入您的问题。。。。") 


if __name__ == '__main__':
    asyncio.run(main())