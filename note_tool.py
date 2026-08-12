"""
NoteTool - 结构化笔记工具
为Agent提供结构化笔记能力，支持：
- 创建/读取/更新/删除笔记
- 按类型组织（任务状态、结论、阻塞项、行动计划等）
- 持久化存储（Markdown格式，带YAML前置元数据）
- 搜索与过滤
- 与MemoryTool集成（可选）

使用场景：
- 长时程任务的状态跟踪
- 关键结论与依赖记录
- 待办事项与行动计划
- 项目知识沉淀

笔记格式示例：
```markdown
---
id: note_20250118_120000_0
title: 项目进展
type: task_state
tags: [milestone, phase1]
created_at: 2025-01-18T12:00:00
updated_at: 2025-01-18T12:00:00
---

# 项目进展

已完成需求分析，下一步：设计方案

## 关键里程碑
- [x] 需求收集
- [ ] 方案设计
"""

from typing import Dict, List, Any
from datetime import datetime
from tool_base import Tool, ToolParameter, tool_action
from pathlib import Path
import json, os, re

class NoteTool(Tool):
    """
    笔记工具
    为 Agent 提供结构化的笔记管理能力
    """

    def __init__(self, 
                workspace = "./notes",
                auto_backup = True,
                max_notes = 1000,
                expandable = False):
        super().__init__(
            name = "note",
            description = "笔记工具 - 创建、读取、更新、删除结构化笔记，支持任务状态、结论、阻塞项等类型"
        )

        self.workspace = Path(workspace)
        self.auto_backup = auto_backup
        self.max_notes = max_notes

        # 确保工作目录存在
        self.workspace.mkdir(parents=True, exist_ok=True)

        # 笔记索引文件
        self.index_file = self.workspace / "notes_index.json"
        self._load_index()

    def _load_index(self):
        """加载笔记索引"""
        if self.index_file.exists():
            with open(self.index_file, "r", encoding="utf-8") as fr:
                self.notes_index = json.load(fr)
        else:
            self.notes_index = {
                "notes": [],
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "total_notes": 0
                }
            }
            self._save_index()

    def _save_index(self):
        """保存笔记索引"""
        with open(self.index_file, "w", encoding="utf-8") as fw:
            json.dump(self.notes_index, fw, ensure_ascii=False, indent=2)

    def _generate_note_id(self):
        """生成笔记ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        count = len(self.notes_index["notes"])
        return f"note_{timestamp}_{count}"

    def _get_note_path(self, note_id: str):
        """获取笔记文件路径"""
        return self.workspace / f"{note_id}.md"

    def _note_to_markdown(self, note: Dict[str, Any]):
        """将笔记对象转换成MARKDOWN格式"""

        # YAML前置元数据
        frontmatter = "---\n"
        frontmatter += f"id: {note['id']}\n"
        frontmatter += f"title: {note['title']}\n"
        frontmatter += f"type: {note['type']}\n"

        if note.get('tags'):
            tags_str = json.dumps(note['tags'])
            frontmatter += "tags: {tags_str}\n"

        frontmatter += f"created_at: {note['created_at']}\n"
        frontmatter += f"updated_at: {note['updated_at']}\n"
        frontmatter += "---\n\n"

        # MarkDown 内容
        content = f"# {note['title']}\n\n"
        content += note['content']

        return frontmatter + content

    def _markdown_to_note(self, markdown_text):
        """将MarkDown文本解析为笔记对象"""
        # 提取YAML前置元数据

        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', markdown_text, re.DOTALL)

        if not frontmatter_match:
            raise ValueError("无效的笔记格式：缺少YAML前置元数据")

        frontmatter_text = frontmatter_match.group(1)
        content_start = frontmatter_match.end()

        # 解析YAML（简化版）
        note = {}
        for line in frontmatter_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                vaule = value.strip()

                # 处理特殊字段
                if key == 'tags':
                    try:
                        note[key] = json.loads(value)
                    except:
                        note[key] = []
                else:
                    note[key] = value

        # 提取内容去掉标题行 
        markdown_content = markdown_text[content_start:].strip()
        # 移除第一行标题
        lines = markdown_content.split('\n')
        if lines and lines[0].startswith('# '):
            markdown_content = '\n'.join(lines[1:]).strip()
        note['content'] = markdown_content

        # 添加元数据
        note['metadata'] = {
            'word_count': len(markdown_content),
            'status': 'active'
        }

        return note

    @tool_action("note_create", "创建一条新的结构化笔记")
    def _create_note(self, params):
        """创建笔记"""
        title = params.get('title')
        content = params.get('content')
        note_type = params.get('note_type', "general")
        tags = params.get('tags', [])

        if not title or not content:
            return "X 创建笔记需要提供标题和内容"

        # 检查笔记数量限制
        if len(self.notes_index["notes"]) >= self.max_notes:
            return f"X 笔记数量已达上限（{self.max_notes}）"

        # 生成笔记ID
        note_id = self._generate_note_id()

        # 创建笔记对象
        note = {
            "id": note_id,
            "title": title,
            "content": content,
            "type": note_type,
            "tags": tags if isinstance(tags, list) else [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "metadata": {
                "word_count": len(content),
                "status": "active"
            }
        }

        # 保存笔记文件（MARKDOWN格式）
        note_path = self._get_note_path(note_id)
        markdown_content = self._note_to_markdown(note)
        with open(note_path, 'w', encoding='utf-8') as fw:
            fw.write(markdown_content)

        # 更新索引文件
        self.notes_index['notes'].append({
            "id": note_id,
            "title": title,
            "content": content,
            "type": note_type,
            "tags": tags if isinstance(tags, list) else [],
            "created_at": datetime.now().isoformat()
        })
        self.notes_index['metadata']['total_notes'] = len(self.notes_index['notes'])
        self._save_index()

        return f"笔记创建成功\nID: {note_id} \ntitle: {title} \ntype: {note_type}"

    @tool_action("note_read", "读取指定ID的笔记")     
    def _read_note(self, params):
        """读取笔记"""
        note_id = params.get("note_id")

        if not note_id:
            return f"X 读取笔记需要提供: {note_id}"

        note_path = self._get_note_path(note_id)
        if not note_path.exists():
            return f"X 笔记不存在: {note_path}"

        with open(note_path, "r", encoding="utf-8") as fr:
            markdown_text = fr.read()

        note = self._markdown_to_note(markdown_text)

        return self._format_note(note)

    @tool_action("note_update", "更新已存在的笔记")
    def _update_note(self, params):
        """更新笔记"""
        note_id = params.get('note_id')

        if not note_id:
            return f"X 更新笔记需要提供: {note_id}"
        
        note_path = self._get_note_path(note_id)
        if not note_path.exists():
            return f"X 笔记不存在: {note_path}"

        # 读取需更新的现有笔记
        with open(note_path, "r", encoding="utf-8") as fr:
            markdown_text = fr.read()

        note = self._markdown_to_note(markdown_text)

        # 更新字段
        if 'title' in params:
            note['title'] = params.get('title')

        if 'content' in params:
            note['content'] = params.get('content')
            note["metadata"]["word_count"] = len(note['content'])
        
        if 'note_type' in params:
            note['type'] = params.get('note_type')

        if 'tags' in params:
            note['tags'] = params['tags'] if isinstance(params['tags'], list) else []

        note["updated_at"] = datetime.now().isoformat()

        # 保存更新
        markdown_content = self._note_to_markdown(note)

        with open(note_path, 'w', encoding="utf-8") as fw:
            fw.write(markdown_content)

        # 更新索引
        for idx_note in self.notes_index["notes"]:
            if idx_note["id"] == note_id:
                idx_note["title"] = note['title']
                idx_note["type"] = note["type"]
                idx_note["tags"] = note["tags"]
                break
        
        self._save_index()

        return f"笔记更新完成: {note_id}"

    @tool_action("note_delete", "删除指定ID的笔记")
    def _delete_note(self, params):
        """删除笔记"""

        note_id = params.get("note_id")
        if not note_id:
            return f"X 删除笔记需要提供: {note_id}"
                
        note_path = self._get_note_path(note_id)
        if not note_path.exists():
            return f"X 笔记不存在: {note_path}"

        # 删除文件
        note_path.unlink()

        # 更新索引
        self.notes_index["notes"] = [
            n for n in self.notes_index["notes"] if n["id"] != note_id
        ]

        self.notes_index["metadata"]["total_notes"] = len(self.notes_index["notes"])
        self._save_index()

        return f"笔记已删除: {note_id}"

    @tool_action("note_list", "列出所有笔记或指定类型的笔记")
    def _list_notes(self, params):
        """列出笔记"""

        note_type = params.get("note_type")
        limit = params.get("limit", 10)

        # 过滤笔记
        filter_notes = self.notes_index["notes"]
        if note_type:
            filter_notes = [n for n in filter_notes if n["type"] == note_type]

        # 限制数量
        filter_notes = filter_notes[:limit]

        if not filter_notes:
            return "暂无笔记"

        # 按更新时间排序
        filter_notes.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

        result = f"笔记列表: (共{len(filter_notes)}条)\n\n"

        for note in filter_notes:
            result += f"* [{note['type']}] {note['title']}\n"
            result += f" ID: {note['note_id']}\n"
            if note.get('tags'):
                result += f" 标签: {note['tags']}\n"
            result += f" 创建时间: {note['created_at']}\n\n"

        return result

    @tool_action("note_search", "搜索包含关键词的笔记")
    def _search_notes(self, params):
        """搜索笔记"""

        query = params.get("query", "").lower()

        limit = params.get("limit", 10)

        if not query:
            return "X 搜索提供 query"

        # 搜索匹配笔记
        match_notes = []

        for note_idx in self.notes_index["notes"]:
            note_path = self._get_note_path(note_idx["id"])
            if note_path.exists():
                with open(note_path, "r", encoding="utf-8") as fr:
                    markdown_text = fr.read()

                try:
                    note = self._markdown_to_note(markdown_text)
                except Exception as e:
                    print (f"解析笔记失败: {note_idx['id']}: {e}")
                    continue

                # 检查标题、内容、标签是否匹配
                if (query in note['title'].lower() or
                    query in note['content'].lower() or 
                    any(query in tag.lower() for tag in note.get("tags", []))):
                    match_notes.append(note)

        # 限制数量
        match_notes = match_notes[:limit]
        if not match_notes:
            return f"未找到匹配的'{query}'笔记"

        result = f"搜索结果: (共{len(match_notes)}条)\n\n"
        for note in match_notes:
            result += self._format_note(note, compact = True) + "\n"

        return result

    @tool_action("note_summary", "获取笔记系统的摘要统计信息")
    def _get_summary(self):
        """获取笔记摘要"""
        total = len(self.notes_index["notes"])
        
        # 按类型统计
        type_counts = {}
        for note in self.notes_index["notes"]:
            note_type = note["type"]
            type_counts[note_type] = type_counts.get(note_type, 0) + 1
        
        result = f"📊 笔记摘要\n\n"
        result += f"总笔记数: {total}\n\n"
        result += "按类型统计:\n"
        for note_type, count in sorted(type_counts.items()):
            result += f"  • {note_type}: {count}\n"
        
        return result

    def _format_note(self, note: Dict[str, Any], compact: bool = False):
        """格式化笔记输出"""
        if compact:
            return (
                f"[{note['type']}] {note['title']}"
                f"ID: {note['id']}\n"
                f"内容: {note['content']}"
            )
        else:
            result = f"笔记详情: \n\n"
            result += f"ID: {note['id']}\n"
            result += f"标题：{note['title']}\n"
            result += f"类型：{note['type']}\n"
            if note.get('tags'):
                result += f"tags: {','.join(note['tags'])}\n"
            result += f"创建时间: {note['created_at']}\n"
            result += f"更新时间: {note['updated_at']}\n"
            result += f"\n内容:\n {note['content']}\n"
        return result

    def run(self, parameters: Dict[str, Any]):
        """执行工具"""

        if not self.validate_parameters(parameters):
            return "x 参数验证失败"

        action = parameters['action']

        if action == "create":
            return self._create_note(parameters)
        elif action == "read":
            return self._read_note(parameters)
        elif action == "update":
            return self._update_note(parameters)
        elif action == "delete":
            return self._delete_note(parameters)
        elif action == "list":
            return self._list_notes(parameters)
        elif action == "search":
            return self._search_notes(parameters)
        elif action == "summary":
            return self._get_summary(parameters)
        else:
            return f"X 不支持该操作: {action}"
        

    def get_parameters(self):
        """获取工具参数定义"""
        return [
            ToolParameter(
                name = "action",
                type = "string",
                description = ("操作类型: create(创建), read(读取), update(更新), "
                    "delete(删除), list(列表), search(搜索), summary(摘要)"),
                required=True
            ),
            ToolParameter(
                name="title",
                type="string",
                description="笔记标题（create/update时必需）",
                required=False
            ),
            ToolParameter(
                name="content",
                type="string",
                description="笔记内容（create/update时必需）",
                required=False
            ),
            ToolParameter(
                name="note_type",
                type="string",
                description=(
                    "笔记类型: task_state(任务状态), conclusion(结论), "
                    "blocker(阻塞项), action(行动计划), reference(参考), general(通用)"
                ),
                required=False,
                default="general"
            ),
            ToolParameter(
                name="tags",
                type="array",
                description="标签列表（可选）",
                required=False
            ),
            ToolParameter(
                name="note_id",
                type="string",
                description="笔记ID（read/update/delete时必需）",
                required=False
            ),
            ToolParameter(
                name="query",
                type="string",
                description="搜索关键词（search时必需）",
                required=False
            ),
            ToolParameter(
                name="limit",
                type="integer",
                description="返回结果数量限制（默认10）",
                required=False,
                default=10
            )
        ]




