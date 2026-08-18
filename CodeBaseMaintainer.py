from typing import Dict, List, Any, Optional
from hello_agent import HelloAgentsLLM
from function_call_agent import FunctionCallAgent
from context import ContextBuilder, ContextConfig, ContextPacket
from note_tool import NoteTool
from terminal_tool import TerminalTool
from memory_tool import MemoryTool
from tool_registry import ToolRegistry
from datetime import datetime
from message import Message
import json



class CodeBaseMaintainer:
    """代码库维护助手"""
    """整合 ContextBuilder 与 NoteTool、TerminalTool、MemoryTool
    实现跨会话的代码库维护管理

    核心特性：
    - Agent 自主使用工具探索代码库
    - 不预定工作流
    - 跨会话记忆和上下文管理
    """

    def __init__(
            self,
            project_name: str,
            codebase_path: str,
            llm: Optional[HelloAgentsLLM] = None):

        self.project_name = project_name
        self.codebase_path = codebase_path
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        #初始化LLM
        self.llm = llm or HelloAgentsLLM()

        # 初始化工具
        self.note_tool = NoteTool(workspace=f"./{project_name}_notes")
        self.terminal_tool = TerminalTool(workspace=codebase_path, timeout=60)

        self.memory_tool = MemoryTool(user_id=project_name, memory_types=["working"])

        # 初始化上下文
        self.context_builder = ContextBuilder(
                                    memory_tool=self.memory_tool,
                                    rag_tool=None,
                                    config = ContextConfig(
                                        max_tokens=4000,
                                        reserve_ratio=0.15,
                                        min_relevance=0.2,
                                        enable_compression=True
                                    )     
                                )

        # 创建工具注册表并注册工具

        self.tool_registry = ToolRegistry()
        self.tool_registry.registry_tool(self.terminal_tool)
        self.tool_registry.registry_tool(self.note_tool)
        self.tool_registry.registry_tool(self.memory_tool)

        # 创建Agent
        self.agent = FunctionCallAgent(
                        name = "CodeBaseMaintainer(Agent)",
                        llm = self.llm,
                        system_prompt = self._build_base_system_prompt(),
                        tool_registry = self.tool_registry,
                        enable_tool_calling = True,
                        max_tool_iterations = 30
                    )

        # 对话历史
        self.conversation_history: List[Message] = []

        # 统计信息
        self.stats = {
            "session_start": datetime.now(),
            "commands_excuted": 0,
            "notes_created": 0,
            "issues_found": 0,
            "tool_calls": 0
        }

        print (f"代码库维护助手已初始化: {project_name} (Agent Mode)")
        print (f"工作目录: {codebase_path}")
        print (f"会话ID: {self.session_id}")
        print (f"可用工具: {','.join(self.tool_registry.list_tools())}")


    def run(self, user_input: str, mode: str = "auto"):
        """
        运行助手: (agentic 方式)

        Args: 
            user_input: 用户输入
            mode: 运行模式提示（给agent提供方向性建议）
                - auto: 自动决策是否使用工具
                - explore: 建议agent侧重代码探索
                - analyze: 建议agent侧重问题分析
                - plan: 建议agent侧重任务规划
        Returns:
            str: 助手的回答 
        """
        print ("===" * 80)
        print (f"用户输入: {user_input}")
        print ("===" * 80)

        # 第一步：检索相关笔记（为Agent提供上下文）
        relevant_notes = self._retrieve_relevant_notes(user_input)
        note_packets = self._notes_to_packets(relevant_notes)

        # 第二步：构建优化后的上下文
        context = self.context_builder.build_context(
            user_query = user_input,
            conversation_history = self.conversation_history,
            system_instructions = self._build_system_instructions(mode),
            additional_packets = note_packets
        )

        # 第三步：让Agent自主决策和使用工具
        print ("让Agent自主决策和使用工具....\n")

        # 更新 Agent 的系统提示（包含上下文）
        self.agent.system_prompt = context

        # 调用 agent 
        response = self.agent.run(user_input)

        # 第四步：调用统计工具
        self._track_tool_usage()

        # 第五步：更新对话历史
        self._update_history(user_input, response)

        print (f"\n助手：{response}")
        print ("===" * 80)

        return response

    def _update_history(self, user_input:str, response: str):
        """更新对话历史"""

        self.conversation_history.append(Message(content=user_input, role="user", timestamp=datetime.now()))
        self.conversation_history.append(Message(content=response, role="assistant", timestamp=datetime.now()))

        # 限制历史长度（保留最近20轮对话）
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

    
    def _track_tool_usage(self):
        """统计工具使用情况"""
        # 从 agent 的执行历史中统计

        if hasattr(self.agent, 'message_history'):
            for msg in self.agent._history[-10:]:
                if msg.role == 'tool':
                    self.stats['tool_calls'] += 1

                    # 根据工具名称统计
                    if 'terminal' in str(msg.content).lower() or 'command' in str(msg.content).lower():
                        self.stats['commands_executed'] += 1
                    elif 'note' in str(msg.content).lower():
                        if 'create' in str(msg.content).lower():
                            self.stats['notes_created'] += 1

    def _notes_to_packets(self, notes: List[Dict]):
        """将笔记转换为上下文包"""
        packets = []

        # 根据笔记类型设置不同的相关性分数
        relevant_map = {
            "blocker": 0.9,
            "action": 0.8,
            "task_state": 0.75,
            "conclusion": 0.7
            }

        for note in notes:
            if not isinstance(note, dict):
                continue

            note_type = note.get("type")
            relevant = relevant_map.get(note_type, 0.6)

            content = f"[笔记: {note.get('title', 'Untitle')}]\n类型: {note_type}\n\n{note.get('content', '')}"
            updated_at = note.get('updated_at')

            try:
                note_timestamp = datetime.fromisoformat(updated_at) if updated_at else datetime.now()
            except (ValueError, TypeError):
                note_timestamp = datetime.now()

            packets.append(ContextPacket(
                content = content,
                timestamp = note_timestamp,
                token_count = len(content) // 4,
                relevance_score = relevant,
                metadata = {
                    "type": "note",
                    "note_type": note_type,
                    "note_id": note.get('id')
                }
            ))

        return packets

    def _normalize_note_results(self, result: Any):
        """将笔记工具的返回值转换为笔记字典列表"""
        if not result:
            return []

        if isinstance(result, dict):
            return [result]

        if isinstance(result, list):
            return [item for item in result if isinstance(item, dict)]

        if isinstance(result, str):
            text = result.strip()
            if not text:
                return []
            if text.startswith("{") or text.startswith("["):
                try:
                    parsed = json.loads(text)
                    return self._normalize_note_results(parsed)
                except Exception as e:
                    print (f"loads failed: {result}")
                    return []

        return []


    
    def _retrieve_relevant_notes(self, user_input:str, limit: int = 3):
        """
        检索相关笔记
        """   
        try:
            # 优先检索 blocker 
            blockers_raw = self.note_tool.run({
                            "action": "list",
                            "note_type": "blocker",
                            "limit": limit
                            })
            
            blockers = self._normalize_note_results(blockers_raw)

            # 搜索相关笔记
            search_result_raw = self.note_tool.run({
                                "action": "search",
                                "query": user_input,
                                "limit": limit
                                })
            search_result = self._normalize_note_results(search_result_raw)

            # 合并去重
            all_notes = {}
            for note in blockers + search_result:
                if not isinstance(note, dict):
                    continue
                note_id = note.get("id")
                if not note_id:
                    continue
                if note_id not in all_notes:
                    all_notes[note_id] = note

            return list(all_notes.values())[:limit]
        except Exception as e:
            print (f"[WARNING] 笔记检索失败: {e}")
            return []       

    def _build_base_system_prompt(self):
        """构建基础系统提示"""
        return f"""
                你是 {self.project_name} 项目的代码库维护助手。
                你的核心能力:
                    1. 使用 TerminalTool 探索代码库
                       - 你可以执行任何 shell 命令: ls, cat, grep, find, git 等
                       - 工作目录: {self.codebase_path}
   
                    2. 使用 NoteTool 记录发现和任务
                       - 创建笔记记录重要发现
                       - 笔记类型: blocker(阻塞问题)、action(行动计划)、task_state(任务状态)、conclusion(结论)
   
                    3. 使用 MemoryTool 存储关键信息
                       - 记住重要的上下文信息
                       - 跨会话保持连贯性

                当前会话ID: {self.session_id}

                重要原则:
                - 你要自主决定使用哪些工具、执行什么命令
                - 探索代码库时，先了解整体结构，再深入细节
                - 发现重要信息时，主动使用 NoteTool 记录
                - 保持回答的专业性和实用性
                """
    
    def _build_system_instructions(self, mode: str):
        """构建系统指令（Agentic 方式）"""
        base_instructions = self._build_base_system_prompt()

        mode_hints = {
            "explore": """
                    用户当前关注: 探索代码库

                    建议策略:
                    - 考虑使用 TerminalTool 了解代码结构（如 find, ls, tree）
                    - 查看关键文件（如 README, 主要模块）
                    - 将架构信息记录到笔记方便后续查阅
                    """,

            "analyze": """
                    用户当前关注: 分析代码质量

                    建议策略：
                    - 考虑使用 grep 查找潜在问题（TODE， FIXME, BUG）
                    - 分析代码复杂度和结构
                    - 将发现的问题记录为 blocker 或 action 笔记
                    """,

            "plan": """
                用户当前关注: 任务规划

                建议策略:
                - 回顾历史笔记了解当前进度
                - 基于已有信息制定行动计划
                - 创建或更新 task_state 类型的笔记
                """,

            "auto": """
                用户当前关注: 自由对话

                建议策略:
                - 根据用户需求灵活决策
                - 在需要时主动使用工具获取信息
                - 不需要时可以直接回答
                """
        }

        return base_instructions + "\n" +  mode_hints.get(mode, mode_hints["auto"])

    # === 便捷方法 ===

    def explore(self, target: str = '.'):
        """
        探索代码库（Agentic 方式）
        """
        return self.run(f"请探索{target}的代码结构, 了解项目的组织方式", model = "explore")

    def analyze(self, focus: str):
        """
        分析代码质量（Agentic 方式）
        Agent 会自主决定如何分析代码质量
        """
        query = f"请分析该代码质量" + (f", 重点关注: {focus}" if focus else "")
        return self.run(query, model = "analyze")

    def plan_next_steps(self, command: str):
        """
        规划下一步任务(Agentic 方式)
        Agent 会查看历史笔记并规划下一步
        """
        return self.run("请根据我们之前的分析和当前进度，规划下一步任务", mode = "plan")

    def excute_command(self, command: str):
        """执行终端命令"""
        result = self.terminal_tool.run({"command": command})
        self.stats["command_excuted"] += 1
        return result

    def create_note(
                self, 
                title: str,
                content: str,
                note_type: str,
                tags: list[str]):
        """创建笔记"""
        result = self.note_tool.run({
            "action": "create",
            "title": title,
            "content": content,
            "note_type": note_type,
            "tags": tags or [self.project_name]
        })
        self.stats["notes_created"] += 1

        return result

    def get_stats(self):
        """获取统计信息"""
        duration = (datetime.now() - self.stats["session_start"]).total_seconds()

        # 获取笔记摘要
        try:
            note_summary = self.note_tool.run({
                "action": "summary"
            })
        except:
            note_summaty = {}

        return {
            "session_info": {
                "session_id": self.session_id,
                "project": self.project_name,
                "duration_seconds": duration
            },
            "activity": {
                "commands_executed": self.stats["commands_executed"],
                "notes_created": self.stats["notes_created"],
                "issues_found": self.stats["issues_found"]
            },
            "notes": note_summary
        }

    def generate_report(self, save_to_file: bool = True):
        """生成简报"""
        report = self.get_stats()

        if save_to_file:
            report_file = f"maintainer_report_{self.session_id}.json"
            with open(report_file, 'w+', encoding='utf-8') as fw:
                json.dumps(report, fw, ensure_ascii=False, indent=2, default=str)
            report["report_file"] = report_file
            print (f"报告已保存：{report_file}")

        return report

def main():
    """主函数：演示 CodeBaseMaintainer 的使用（Agentic 版本）"""

    """
    在这个版本中：
    - Agent 自主决定使用哪些工具
    - 不预定工作流
    - Agent 根据需要灵活探索代码库
    """

    print ("===" * 80)
    print ("演示 CodeBaseMaintainer 的使用（Agentic 版本）")
    print ("===" * 80 + '\n\n')

    # 初始化助手
    maintainer = CodeBaseMaintainer(
        project_name = "hello_agent_repo",
        codebase_path = "./../hello_agent/",
        llm = HelloAgentsLLM()
    )

    # 探索代码库
    print ("\n#### 探索代码库（Agent 自主探索）###\n")
    response = maintainer.explore()
    print (f"代码库信息：{response}")

if __name__ == "__main__":
    main()



