import os
from typing import Optional, List, Any, Dict

from tool_base import Tool

from tool_registry import ToolRegistry

class SearchTool(Tool):

    def __init__(self, name, description):
        self.name = "search_tool"
        self.description = "智能搜索工具，支持多个搜索源，自动选择最佳"
        self.search_sources = []
        self.setup_search_sources()

    def setup_search_sources(self):
        """设置搜索源"""

        if os.getenv("TAVILY_API_KEY"):
            try:
                from tavily import TavilyClient
                self.tavily_client = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))
                self.search_sources.append('tavily')
                print ("已开启Tavily搜索源！")
            except Exception as e:
                raise e
                print (f"开启Tavily搜索源失败: {e}")

        if os.getenv("SERPAPI_API_KEY"):
            try:
                self.search_sources.append("serpapi")
                print ("已开启serpapi搜索源！")
            except Exception as e:
                raise e
                print (f"开启serpapi搜索源失败: {e}")

        if self.search_sources:
            print (f"可用搜索源：{','.join(self.search_sources)}")
        else:
            print ("没有可用的搜索源，请配置搜索源！")

    def run(self, parameters: Dict[str, Any]):
        if not parameters or 'query' not in parameters:
            return "没有需要搜索的！"

        query = parameters['query'].strip()

        if not query:
            return "query不能为空"

        result = self.search(query)
        return result

    def search(self, query):
        """执行智能搜索"""
        if not query.strip():
            return "ERROR: 搜索查询不能为空"

        if not self.search_sources:
            return "ERROR: 搜索源不能为空"
        
        print (f"开始智能搜索-------query: {query}")

        for source in self.search_sources:
            if source == "tavily":
                result = self.search_api_tavily(query)
                if result and "未找到" not in result:
                    return f"Tavily AI搜索结果：\n\n{result}"
                
                elif source == "serpapi":
                    result = self.search_api_serpapi(query)
                    if result and "未找到" not in result:
                        return f"SerpApi AI搜索结果：\n\n{result}\n"

        return "所有搜索源都搜索失败"


    def search_api_tavily(self, query):
        try:
            response = self.tavily_client.search(query, max_results=3)
        except Exception as e:
            raise e
            print (f"调用tavily client 搜索出现问题：{e}")
            return f"调用tavily client 搜索出现问题：{e}"
        

        if response.get('answer'):
            result = f"AI直接答案：{response['answer']}"
        else:
            result = ""

        result += ""

        for i, item in enumerate(response.get('result', [])[:3], 1):
            result += f"[{i}] {item.get('title', '')}\n"
            result += f"  {item.get('content', '')[:300]}...\n"

        return result

    def search_api_serpapi(self, query):
        import serpapi

        try:
            search = serpapi.GoogleSearch({
                    "q":query,
                    "api_key": os.getenv("SERPAPI_API_KEY"),
                    "num":3
                    })
        except Exception as e:
            raise e
            print (f"调用serpapi搜索出现问题：{e}")
            return f"调用serpapi搜索出现问题：{e}"

        results = search.get_dict()

        result = "Google 搜索结果：\n"
        if "organic_results" in results:
            for i, res in enumerate(results["organic_results"][:3], 1):
                result += f"[{i}] {res.get('title', '')}\n"
                result += f"    {res.get('snippet', '')}\n\n"

        return result

    def get_parameters(self):
        tool_params = []
        cal_tool_params = ToolParameter(self.name, "str", self.description)
        tool_params.append(cal_tool_params)
        return tool_params








