"""FunctionCallAgent - 使用OpenAI函数调用范式的Agent实现"""

from __future__ import annotations
import json
from typing import Iterator, Optional, Union, TYPE_CHECKING, Any, List, Dict

from agent_base import Agent
from config import Config
from hello_agent import HelloAgentsLLM
from message import Message
from tool_registry import ToolRegistry

def _map_parameter_type(type):
    """将工具参数类型映射为JSON Schema允许的类型"""
    normalized = (type or "").lower()

    if normalized in {"string", "number", "integer", "boolean", "any", "object"}:
        return normalized

    return "string"


class FunctionCallAgent(Agent):
    """基于OpenAI原生函数调用机制的Agent"""

    def __init__(
            self, 
            name: str, 
            llm: HelloAgentsLLM, 
            system_prompt: Optional[str] = None, 
            config: Optional[Config] = None,
            tool_registry: Optional["ToolRegistry"] = None,
            enable_tool_calling: bool = True,
            default_tool_choice: Union[str, dict] = "auto",
            max_tool_iterations: int = 3
            ):
        super().__init__(name, llm, system_prompt, config)

        self.tool_registry = tool_registry
        self.enable_tool_calling = enable_tool_calling
        self.default_tool_choice = default_tool_choice
        self.max_tool_iterations = max_tool_iterations

    def _get_system_prompt(self):
        """构建系统提示词"""
        base_prompt = self.system_prompt or """
                    你是一个可靠的AI助手，能够在需要时调用工具完成任务
                    """
        if not self.enable_tool_calling or not self.tool_registry:
            return base_prompt

        tools_description = self.tool_registry.get_tools_description()
        if not tools_description or tools_description == "暂无可用工具":
            return base_prompt

        prompt = base_prompt + "\n\n ## 可用工具 \n"
        prompt += "当你判断需要外部信息或执行动作时，可以直接通过函数调用使用以下工具: \n"
        prompt += tools_description + "\n"
        prompt += "\n 请你主动决定是否调用工具，合理利用多次调用来获取完备的答案。"
        return prompt
    
    def _build_tools_schemas(self):
        if not self.enable_tool_calling or not self.tool_registry:
            return []

        schemas: list[dict[str, Any]] = []

        # Tool 对象
        for tool in self.tool_registry.get_all_tools():
            properties: Dict[str, Any] = {}

            required: list[str] = []
            try:
                parameters = tool.get_parameters()
            except Exception as e:
                parameters = []
                print (f"{tool} 获取参数失败：{e}")

            for params in parameters:
                properties[params.name] = {
                    "type": _map_parameter_type(params.type),
                    "description": params.description or ""
                }

                if params.default is not None:
                    properties[params.name]["default"] = params.default

                if getattr(params, "required", True):
                    required.append(params.name)

            schema: dict[str, Any] = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": {
                        "type": "object",
                        "properties": properties
                    }
                }
            }

            if required:
                schema["function"]["parameters"]["required"] = required

            schemas.append(schema)

        # register_function 注册的工具(直接访问内部结构)
        function_map = getattr(self.tool_registry, "_functions", {})
        for name, info in function_map.items():
            schemas.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": info.get("description", ""),
                    "parameters":{
                        "type": "object",
                        "properties": {
                            "input": {
                                "type": "string",
                                "description": "输入文本"
                            }
                        },
                        "required": ["input"]
                    }
                }
            })
            
        return schemas

    @staticmethod
    def _parse_function_call_arguments(arguments):
        """解析模型返回的JSON字符串参数"""

        if not arguments:
            return {}

        try:
            parsed = json.loads(arguments)
            return parsed if isinstance(parsed, dict) else {}
        except Exception as e:
            print (f"loads 参数失败: {e}")
            return {}

    @staticmethod
    def _extract_message_content(raw_content: Any):
        """从OpenAI 响应的message.content中安全提取文本"""
        if raw_content is None:
            return ""
        if isinstance(raw_content, str):
            return raw_content
        if isinstance(raw_content, list):
            parts: list[str] = []
            for item in raw_content:
                text = getattr(item, "text", None)
                if text is None and isinstance(item, dict):
                    text = item.get("text")
                if text:
                    parts.append(text)
            return "".join(parts)
        return str(raw_content)

    def _convert_parameter_types(self, tool_name: str, param_dict: dict[str, Any]):
        """根据工具定义尽可能转参数类型"""
        if not param_dict:
            return {}

        if not self.tool_registry:
            return param_dict

        tool = self.tool_registry.get_tool(tool_name)
        if not tool:
            return param_dict

        try:
            tool_params = tool.get_parameters()
        except Exception as e:
            print (f"获取工具{tool_name}参数失败: {e}")
            return param_dict

        typing_mapping = {param.name: param.type for param in tool_params}

        converted: dict[str, Any] = {}

        for key, value in typing_mapping.items():
            param_type = typing_mapping.get(key)
            if not param_type:
                continue

            try:
                normalized = param_type.lower()
                if normalized in {"number", "float"}:
                    converted[key] = float(value)
                elif normalized in {"integer", "int"}:
                    converted[key] = int(value)
                elif normalized in {"boolean", "bool"}:
                    if isinstance(value, bool):
                        converted[key] = value
                    elif isinstance(value, (int, float)):
                        converted[key] = bool(value)
                    elif isinstance(value, str):
                        converted[key] = value.lower() in {"true", "1", "yes"}
                    else:
                        converted[key] = bool(value)
                else:
                    converted[key] = value
            except (TypeError, ValueError) as e:
                print(f"type:{param_type} , error: {e}")
                converted[key] = value

        return converted

    
    def _execute_tool_call(self, tool_name: str, arguments: dict[str, Any]):
        """执行工具调用并返回字符串结果"""
        if not self.tool_registry.get_tool(tool_name):
            return "X 错误：未配置工具注册表"

        tool = self.tool_registry.get_tool(tool_name)
        if tool:
            try:
                typed_arguments = self._convert_parameter_types(tool_name, arguments)
                return tool.run(typed_arguments)
            except Exception as e:
                print (f"X 工具{tool_name}调用失败: {e}")
                return f"X 工具{tool_name}调用失败: {e}"

        func = self.tool_registry.get_function(tool_name)
        if func:
            try:
                input_text = arguments.get("input", "")
                return func
            except Exception as e:
                print (f"X 工具{tool_name}调用失败: {e}") 
                return f"X 工具{tool_name}调用失败: {e}"

        return f"X 错误：未找到工具: {tool_name}"


    def _invoke_with_tools(
                        self, 
                        messages: List[dict[str, Any]], 
                        tools: List[dict[str, Any]],
                        tool_choice: Union[str, dict],
                        **kwargs):
        """调用OpenAI客户端执行函数调用"""
        client = getattr(self.llm, "client", None)
        if client is None:
            raise RuntimeError("HelloAgentsLLM 未初始化客户端，无法执行函数调用。")

        client_kwargs = dict(kwargs)

        
        if hasattr(self.llm, "temperature"):
            client_kwargs.setdefault("temperature", self.llm.temperature)

        if hasattr(self.llm, "max_token") and self.llm.max_token is not None:
            client_kwargs.setdefault("max_token", self.llm.max_tokens)

        return client.chat.completions.create(
                    model = self.llm.model,
                    messages=messages,
                    tools = tools,
                    tool_choice = tool_choice,
                )

        return client.chat.completions.create(
            model = self.llm.model,
            messages=messages,
            tools = tools,
            tool_choice = tool_choice,
            **client_kwargs
        )

    
    def run(
            self,
            input_text,
            *,
            max_tool_iterations:Optional[int] = None,
            tool_choice: Optional[Union[str, dict]] = None,
            **kwargs):

        """执行函数调用范式的对话流程"""

        message: list[dict[str, Any]] = []

        system_prompt = self._get_system_prompt()

        message.append({"role": "system", "content": system_prompt})

        for msg in self._history:
            message.append({"role": msg.role, "content": msg.content})

        message.append({"role": "user", "content": input_text})

        tool_schemas = self._build_tools_schemas()

        if not tool_schemas:
            response_text = self.llm.invoke(message, **kwargs)
            self.add_message(Message(input_text, "user"))
            self.add_message(Message(response_text, "assistant"))
            return response_text

        iterations_limit = max_tool_iterations if max_tool_iterations is not None else self.max_tool_iterations

        effective_tool_choice: Union[str, dict] = tool_choice if tool_choice is not None else self.default_tool_choice

        current_iteration = 0

        final_answer = ""

        while current_iteration < iterations_limit:
            response_text = self._invoke_with_tools(
                message,
                tools=tool_schemas,
                tool_choice = effective_tool_choice,
                **kwargs
            )
            choice = response_text.choices[0]
            assistant_message = choice.message
            content = self._extract_message_content(assistant_message.content)
            tool_calls = list(assistant_message.tool_calls or [])

            if tool_calls:
                assistant_payload: dict[str, Any] = {"role": "assistant", "content": content}
                assistant_payload["tool_calls"] = []

                for tool_call in tool_calls:
                    assistant_payload["tool_calls"].append({
                        "id": tool_call.id,
                        "type": tool_call.type,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    })
                message.append(assistant_payload)

                for tool_call in tool_calls:
                    tool_name = tool_call.function.name
                    arguments = self._parse_function_call_arguments(tool_call.function.arguments)

                    result = self._execute_tool_call(tool_name, arguments)
                    message.append({
                        "role": "tool",
                        "content": result,
                        "name": tool_name,
                        "tool_call_id": tool_call.id
                    })

                current_iteration += 1
                continue

            final_answer = content
            message.append({"role": "assistant", "content":final_answer})
            break

        if current_iteration >= iterations_limit and not final_answer:
            final_choice = self._invoke_with_tools(
                message,
                tools = tool_schemas,
                tool_choice = "none",
                **kwargs
            )
            final_answer = self._extract_message_content(final_choice.choices[0].message.content)
            message.append({"role": "assistant", "content": content})

        self.add_message(Message(input_text, "user"))
        self.add_message(Message(final_answer, "assistant"))
        return final_answer

    def add_tool(self, tool):
        """便捷方法：将工具注册到当前agent"""

        if not self.tool_registry:
            self.tool_registry = ToolRegistry()
            self.enable_tool_calling = True

        if hasattr(tool, "auto_expand") and getattr(tool, "auto_expand"):
            expanded_tools = tool.get_expanded_tools()
            if expanded_tools:
                for expanded_tool in expanded_tools:
                    self.tool_registry.registry_tool(expanded_tool)
                print (f"MCP 工具 '{tool.name}' 已展开为 {len(expanded_tools)}个独立工具")
                return

        self.tool_registry.registry_tool(tool)

    def remove(self, tool_name):
        if self.tool_registry:
            before = set(self.tool_registry.list_tools())
            self.tool_registry.unregister(tool_name)
            after = set(self.tool_registry.list_tools())

            return tool_name in before and tool_name not in after

        return False

    def list_tools(self):
        if self.tool_registry:
            return self.tool_registry.list_tools()
        return []

    def has_tool(self):
        return self.enable_tool_calling and self.tool_registry is not None

    def stream_run(self, input_text: str, **kwargs):
        """流式调用未实现，直接回退到一次性调用"""
        result = self.run(input_text, **kwargs)
        yield result




        


        

