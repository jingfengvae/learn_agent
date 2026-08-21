from typing import Optional, Iterator, TYPE_CHECKING, Callable

from agent_base import Agent
from config import Config
from message import Message
from tool_registry import ToolRegistry
import json

import re

from hello_agent import HelloAgentsLLM

class SimpleAgent(Agent):
    """docstring for SimpleAgent"""
    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None, 
        tool_registry: Optional['tool_registry'] = None,
        enable_tool_calling: bool = True,
        tool_confirm_callback: Optional[Callable[[str, dict], bool]] = None):
        super().__init__(name, llm, system_prompt, config)
        self.tool_registry = tool_registry
        self.enable_tool_calling = enable_tool_calling and tool_registry is not None
        self.tool_confirm_callback = tool_confirm_callback

    def _get_enhance_system_prompt(self):
        """构建增强的系统提示词，包含工具信息"""

        base_prompt = self.system_prompt or "你是一个有用的AI助手。"

        if not self.enable_tool_calling or not self.tool_registry:
            return base_prompt

        # 获取工具描述
        tools_description = self.tool_registry.get_tools_description()
        if not tools_description or tools_description == "暂无可用工具":
            return base_prompt

        tools_section = "\n\n## 可用工具\n"
        tools_section += "你可以使用以下工具来帮助回答问题：\n"
        tools_section += tools_description + "\n"

        tools_section += "\n## 工具调用格式\n"
        tools_section += "当需要使用工具时，请使用以下格式：\n"
        tools_section += "`[TOOL_CALL:{tool_name}:{parameters}]`\n\n"

        tools_section += "### 参数格式说明\n"
        tools_section += "1. **多个参数**：使用 `key=value` 格式，用逗号分隔\n"
        tools_section += "   示例：`[TOOL_CALL:calculator_multiply:a=12,b=8]`\n"
        tools_section += "   示例：`[TOOL_CALL:filesystem_read_file:path=README.md]`\n\n"
        tools_section += "2. **单个参数**：直接使用 `key=value`\n"
        tools_section += "   示例：`[TOOL_CALL:search:query=Python编程]`\n\n"
        tools_section += "3. **简单查询**：可以直接传入文本\n"
        tools_section += "   示例：`[TOOL_CALL:search:Python编程]`\n\n"

        tools_section += "### 重要提示\n"
        tools_section += "- 参数名必须与工具定义的参数名完全匹配\n"
        tools_section += "- 数字参数直接写数字，不需要引号：`a=12` 而不是 `a=\"12\"`\n"
        tools_section += "- 文件路径等字符串参数直接写：`path=README.md`\n"
        tools_section += "- 工具调用结果会自动插入到对话中，然后你可以基于结果继续回答\n"

        return base_prompt + tools_section

    def _parse_tool_call(self, text):
        """解析文本中的工具"""

        pattern = r"\[TOOL_CALL:([^:]+):([^\]]+)\]"

        matchs = re.findall(pattern, text)

        tool_calls = []

        for tool_name, parameters in matchs:
            tool_calls.append({
                "tool_name": tool_name,
                "parameters": parameters,
                "origin": f"[TOOL_CALL: {tool_name}:{parameters}]"
                })
        
        return tool_calls

    def _execute_tool_call(self, tool_name, parameters):
        """执行工具调用"""
        if not self.tool_registry:
            return f"ERROR: 未配置工具注册表"

        try:
            tool = self.tool_registry.get_tool(tool_name)

            if not tool:
                return f"ERROR: 未找到工具{tool_name}"
            
            """解析工具参数"""
            param_dict = self._parse_tool_call(tool_name, parameters)
            
            if self.tool_confirm_callback is not None:
                try:
                    allowed = bool(self.tool_confirm_callback(tool_name, param_dict))
                except Exception as e:
                    return f"工具调用确认失败：{e}"

                if not allowed:
                    return f"已取消本次工具调用"

            result = tool.run(param_dict)
            return f"工具: {tool_name} 执行结果: {result}"

        except Exception as e:
            return f"工具调用失败：{str(e)}"


    def _parse_tool_parameters(self, tool_name, parameters):
        """智能解析工具参数"""
        
        param_dict = {}

        if parameters.strip().startswith("{"):
            try:
                param_dict = json.load(parameters)
                param_dict = self._convert_parameter_types(tool_name, param_dict)
                return param_dict
            except json.JSONDecodeError as e:
                print (f"json: {parameters} 解析失败")
                pass 
        
        if '=' in parameters:

            if ',' in parameters:
                pairs = parameters.strip().split(',')
               
                for pair in pairs:
                    key, value = pair.strip().split('=', 1)
                    param_dict[key.strip()] = value.strip()

            else:
                key, value = parameters.strip().split('=', 1)
                param_dict[key.strip()] = value.strip()

            param_dict = self._convert_parameter_types(tool_name, param_dict)

            if 'action' not in param_dict:
                param_dict = self._infer_action(tool_name, param_dict)

        else:
            param_dict = self._infer_simple_parameters(tool_name, parameters)

        return param_dict

    def _convert_parameter_types(self, tool_name, param_dict):
        
        """
        根据工具的参数定义转换参数类型

        Args:
            tool_name: 工具名称
            param_dict: 参数字典

        Returns:
            类型转换后的参数字典
        """

        if not self.tool_registry:
            return param_dict

        tool = self.tool_registry.get_tool(tool_name)

        if not tool:
            return param_dict

        try:
            tool_params = tool.get_parameters()
        except Exception as e:
            return param_dict

        param_types = {}
        
        for param in tool_params:
            param_types[param.name] = param.type

        converted_dict = {}

        for key, value in param_dict.items():
            if key in param_types:
                param_type = param_types[key]

                try:
                    if param_type == "number" or param_type == "integer":
                        if isinstance(value, str):
                            converted_dict[key] = float(value) if param_type == "number" else int(value)
                        else:
                            converted_dict[key] = value
                    elif param_type == "boolean":
                        if isinstance(value, str):
                            converted_dict[key] = value.lower() in ('true', '1', 'yes')
                        else:
                            converted_dict[key] = bool(value)
                    else:
                        converted_dict[key] = value 
                except (ValueError, TypeError) as e:
                    print (f"转换类型Error, {e}")
                    converted_dict[key] = value
            else:
                converted_dict[key] = value

        return converted_dict

    def _infer_action(self, tool_name, param_dict):
        """根据工具类型和参数推断action"""
        
        if tool_name == 'memory':
            if 'recall' in param_dict:
                param_dict['action'] = 'search'
                param_dict['query'] = param_dict.pop('recall')
            elif 'store' in param_dict:
                param_dict['action'] = 'add'
                param_dict['content'] = param_dict.pop('store')
            elif 'query' in param_dict:
                param_dict['action'] = 'search'
            elif 'content' in param_dict:
                param_dict['action'] = 'add'
        elif tool_name == 'rag':
            if 'search' in param_dict:
                param_dict['action'] = 'search'
                param_dict['query'] = param_dict.pop('search')
            elif 'query' in param_dict:
                param_dict['action'] = 'search'
            elif 'text' in param_dict:
                param_dict['action'] = 'add_text'

        return param_dict

    def _infer_simple_parameters(self, tool_name, parameters):
        """为简单参数推断完整的参数字典"""
        
        if tool_name == 'rag':
            return {'action': 'search', 'query': parameters}
        elif tool_name == 'memory':
            return {'action': 'search', 'query': parameters}
        else:
            return {'input': parameters}

    def run(self, input_text: str, max_tool_iterations: int = 5, **kwargs):
        """
        运行SimpleAgent，支持可选的工具调用
        
        Args:
            input_text: 用户输入
            max_tool_iterations: 最大工具调用迭代次数（仅在启用工具时有效）
            **kwargs: 其他参数
            
        Returns:
            Agent响应
        """

        # 构建消息列表

        messages = []

        enhance_system_prompt = self._get_enhance_system_prompt()

        messages.append({"role": "system", "content": enhance_system_prompt})

        # 添加历史消息
        for msg in self._history:
            messages.append({"role": msg.role, "content": msg.content})

        # 添加当前用户消息
        messages.append({"role": "user", "content": input_text})

        if not self.enable_tool_calling:
            response = self.llm.invoke(messages, **kwargs)
            self.add_messages([Message(input_text, "user")])
            self.add_messages([Message(response, "assistant")])
            return response

        current_iteration = 0

        final_answer = ""

        while current_iteration < max_tool_iterations:
            
            response = self.llm.invoke(messages, **kwargs)

            tool_calls = self._parse_tool_call(response)

            if tool_calls:
                tool_results = []

                clean_response = response

                for call in tool_calls:
                    result = self._execute_tool_call(call['tool_name'], call['parameters'])

                    tool_results.append(result)

                    clean_response = clean_response.replace(call['origin'], '')

                messages.append({"role": "assistant", "content": clean_response})

                tool_results_text = "\n\n".join(tool_results)

                messages.append({"role": "user", "content": f"工具执行结果：\n{tool_results_text}\n\n 请基于以上内容给出完整回答"})

                current_iteration += 1
                continue

            final_answer = response
            break
        
        # 如果超过最大迭代次数，获取最后一次回答
        if current_iteration >= max_tool_iterations and not final_answer:
            final_answer = self.llm.invoke(messages, **kwargs)
        
        # 保存到历史记录
        self.add_message(Message(input_text, "user"))
        self.add_message(Message(final_answer, "assistant"))

        return final_answer

    def add_tool(self, tool):
        """
        添加工具到Agent（便利方法）

        如果是MCP工具且启用了auto_expand，会自动展开为多个独立工具
        """
        if not self.tool_registry:
            self.tool_registry = ToolRegistry()
            self.enable_tool_calling = True

        # 检查是否是MCP工具且需要展开
        if hasattr(tool, 'auto_expand') and tool.auto_expand:
            # 获取展开的工具列表
            expanded_tools = tool.get_expanded_tools()
            if expanded_tools:
                # 注册所有展开的工具
                for expanded_tool in expanded_tools:
                    self.tool_registry.registry_tool(expanded_tool)
                print(f"✅ MCP工具 '{tool.name}' 已展开为 {len(expanded_tools)} 个独立工具")
                return

        # 普通工具或不展开的MCP工具
        self.tool_registry.registry_tool(tool)
        print(f"🔧 工具 '{tool.name}' 已添加")

    def remove_tool(self, tool_name):
        """移除工具（便利方法）"""
        if self.tool_registry:
            return self.tool_registry.unregister_tool(tool_name)
        return False

    def list_tools(self):
        """列出所有可用工具"""
        if self.tool_registry:
            return self.tool_registry.list_tools()
        return []

    def has_tools(self):
        """检查是否有可用工具"""
        return self.enable_tool_calling and self.tool_registry is not None

    def stream_run(self, input_text, **kwargs):
        """
        流式运行Agent
        
        Args:
            input_text: 用户输入
            **kwargs: 其他参数
            
        Yields:
            Agent响应片段
        """
        # 构建消息列表
        messages = []
        
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        
        for msg in self._history:
            messages.append({"role": msg.role, "content": msg.content})
        
        messages.append({"role": "user", "content": input_text})
        
        # 流式调用LLM
        full_response = ""
        for chunk in self.llm.stream_invoke(messages, **kwargs):
            full_response += chunk
            yield chunk
        
        # 保存完整对话到历史记录
        self.add_message(Message(input_text, "user"))
        self.add_message(Message(full_response, "assistant"))
        print(f"✅ {self.name} 流式响应完成")


    
