from serpapi import SerpApiClient

from typing import Dict, List

def search(query):

    print (f"正在执行serpapi搜索：{query}......")

    try:
        api_key = "63e2607c703a98ed060494583b5a2f55522af8998a6ef0f8b66eda358aaa8af0"

        params = {
                "engine": "google",
                "q" : query,
                "api_key": api_key,
                "gl": "cn",
                "hl": "zh-cn"
        }

        client = SerpApiClient(params)

        results = client.get_dict()

        if "answer_box_list" in results:
            return "\n\n".join(results["answer_box_list"])

        if "answer_box" in results and "answer" in results["answer_box"]:
            return results["answer_box"]["answer"]

        if "knowledge_graph" in results and "description" in results["knowledge_graph"]:
            return results["knowledge_graph"]["description"]

        if "organic_results" in results and results["organic_results"]:
            snippets = [
                    f"[{i + 1}] {res.get('title', '')} \n {res.get('snippet', '')}"
                    for i, res in enumerate(results["organic_results"][:3])
            ]

            return "\n\n".join(snippets)
    except Exception as e:
        return ("调用serpapi是搜索{query}发生Error")



class ToolExecutor:

    def __init__(self):

        self.tools : Dict[str, Dict[str, Any]] = {}

    def registerTool(self, name, description, func):
        """
        向工具箱注册一个新工具
        """

        if name in self.tools:
            print (f"警告： {name} 工具已存在, 将被覆盖！！！")

        self.tools[name] = {"description": description, "func": func}

        print (f"工具{name}已注册~~")


    def getTool(self, name):
        """
        根据名称获取一个工具的执行函数
        """

        return self.tools.get(name, {}).get("func")

    def getAvailableTools(self):

        """
        获取所有可用工具的格式化描述字符串
        """
        return "\n".join([
            f"--{name}: {info['description']}"
            for name, info in self.tools.items()    
            ])


if __name__ == '__main__':
    
    toolExecutor = ToolExecutor()

    search_decription = "一个网页搜索引擎，当你需要回答关于时事、事实以及在你的知识库找不到信息时，应使用此工具。"

    toolExecutor.registerTool("Serach", search_decription, search)

    """
    打印可用的工具
    """
    print ("--可用的工具--")
    print (toolExecutor.getAvailableTools())

    """
    智能体Action的调用，这次问一个时事性的问题
    """

    print ("\n---执行Action: Search['英伟达最新的GPU型号是什么']--")

    tool_name = "Serach"

    tool_input = "英伟达最新的GPU型号是什么"

    tool_function = toolExecutor.getTool(tool_name)

    if tool_function:
        observation = tool_function(tool_input)
        print ("---(观察) Observation---")
        print (observation)

    else:
        print (f"未找到工具: {tool_name}")



    