import os
import time
from typing import Dict, Any, List, Optional
from hello_agent import HelloAgentsLLM
from tool_base import Tool, ToolParameter, tool_action
from rag_pipeline import create_rag_pipeline

class RAGTool(Tool):
    """docstring for RAGTool"""
    def __init__(self, 
                knowledge_base_path: str = './knowledge_base',
                qdrant_url: str = None,
                qdrant_api_key: str = None,
                collection_name: str = "rag_knowledge_base",
                rag_namespace: str = "default",
                expandable: bool = False):

        super().__init__(name="rag", 
                        description="RAG工具 - 支持多格式文档检索增强生成，提供智能问答能力",
                        expandable = expandable)

        self.knowledge_base_path = knowledge_base_path
        self._pipelines: Dict[str, Dict[str, Any]] = {}
        
        self.qdrant_url = qdrant_url or os.getenv("QDRAND_URL")
        self.qdrant_api_key = qdrant_api_key or os.getenv("QDRAND_API_KEY")
        self.collection_name = collection_name
        self.rag_namespace = rag_namespace
        
        os.makedirs(knowledge_base_path, exist_ok=True)

        self._init_components()
        

    def _init_components(self):
        """初始化RAG组件"""
        try:
            default_pipeline = create_rag_pipeline(
                            qdrant_url = self.qdrant_url,
                            qdrant_api_key = self.qdrant_api_key,
                            collection_name = self.collection_name,
                            rag_namespace = self.rag_namespace)

            self.initialized = True
 
            self._pipelines[self.rag_namespace] = default_pipeline
 
            self.llm = HelloAgentsLLM()
 
            print (f"RAG工具初始化成功: namespace = {self.rag_namespace}, collection = {self.collection_name}")
        except Exception as e:
            self.initialized = False
            self.init_error = str(e)
            print (f"RAG工具初始化失败: {str(e)}")


    def get_pipeline(self, namespace: Optional[str] = None):
        target_ns = namespace or self.rag_namespace

        if target_ns in self._pipelines:
            return self._pipelines[target_ns]

        pipeline = create_rag_pipeline(qdrant_url = self.qdrant_url,
                                    qdrant_api_key = self.qdrant_api_key,
                                    collection_name = self.collection_name,
                                    rag_namespace = target_ns)
        self._pipelines[target_ns] = pipeline
        return pipeline

    def run(self, parameters: Dict[str, Any]):

        print (f"->>>>>>>>>>>>>>>>>>>RAG工具运行参数: {parameters}")

        if not self.validate_parameters(parameters):
            return f"{parameters} --> 参数验证Error: 缺少必要的参数"

        action = parameters.get("action")

        print (f"RAG工具执行操作: {action}, 参数: {parameters}")

        try:
            if action == "add_document":
                return self._add_document(file_path = parameters.get("file_path"),
                                        document_id = parameters.get("document_id"),
                                        namespace = parameters.get("namespace", "default"),
                                        chunk_size = parameters.get("chunk_size", 800),
                                        chunk_overlap = parameters.get("chunk_overlap", 100))
            elif action == "add_text":
                return self._add_text(text = parameters.get("text"),
                                    document_id = parameters.get("document_id"),
                                    namespace = parameters.get("namespace", "default"),
                                    chunk_size = parameters.get("chunk_size", 800),
                                    chunk_overlap = parameters.get("chunk_overlap", 100))
            elif action == "ask":
                question = parameters.get("question") or parameters.get("query")
                print ("************", f"智能问答: {question}", f"参数: {parameters}")
                return self._ask(question = question, 
                                limit = parameters.get("limit", 5),
                                enable_advanced_search = parameters.get("enable_advanced_search", True),
                                include_citations = parameters.get("include_citations", True),
                                max_chars = parameters.get("max_chars", 1200),
                                namespace = parameters.get("namespace", "default"))
            elif action == "search":
                query = parameters.get("question") or parameters.get("query")
                return self._search(query = query, 
                                limit = parameters.get("limit", 5),
                                min_score = parameters.get("min_score", 0.1),
                                enable_advanced_search = parameters.get("enable_advanced_search", True),
                                max_chars = parameters.get("max_chars", 1200),
                                include_citations = parameters.get("include_citations", True),
                                namespace = parameters.get("namespace", "default"))
            elif action == "stats":
                return self._get_stats(namespace = parameters.get("namespace", "default"))
            elif action == "clear":
                return self._clear_knowledge_base(config = parameters.get("config", False),
                                                namespace = parameters.get("namespace", "default"))
            else:
                return f"不支持的操作: {action}"
        except Exception as e:
            return f"执行操作: {action} 时发生Error"

    def get_parameters(self):
        return [
                ToolParameter(
                            name = "action",
                            type = "string",
                            description = "操作类型: add_document(添加文档), add_text(添加文本), ask(智能回答), search(搜索), stats(统计), clear(清空)",
                            required = True
                            ),

                ToolParameter(
                            name = "file_path",
                            type = "string",
                            description = "文档文件路径: (支持PDF、Word、Excel、PPT、图片、音频等多种格式)",
                            required = False
                            ),

                ToolParameter(
                            name = "text",
                            type = "string",
                            description = "要添加的文本内容",
                            required = False
                            ),
                ToolParameter(
                            name = "question",
                            type = "string",
                            description = "用户问题(用于智能回答)",
                            required = False
                            ),
                ToolParameter(
                            name = "query",
                            type = "string",
                            description = "搜索查询词(用于基础搜索)",
                            required = False
                            ),
                ToolParameter(
                            name = "namespace",
                            type = "string",
                            description = "知识库的命名空间(用于隔离不同项目, 默认: default)",
                            required = False
                            ),
                ToolParameter(
                            name = "limit",
                            type = "integer",
                            description = "返回结果数量(默认: 5)",
                            required = False
                            ),
                ToolParameter(
                            name = "include_citations",
                            type = "boolean",
                            description = "是否包含引用来源(默认: true)",
                            required = True
                            )
                ]

    @tool_action("rag_namespace", "添加文档到知识库（支持PDF、Word、Excel、PPT、图片、音频等多种格式）")
    def _add_document(self, file_path: str, 
                            document_id: str = None,
                            namespace: str = "default",
                            chunk_size: int = 800,
                            chunk_overlap: int = 100):

        try:
            if not file_path or not os.exist.path(file_path):
                return f"文件不存在: {file_path}"
            
            print ("+++++++++++++++++++++++++++++++++++++")

            pipeline = self.get_pipeline(namespace)

            t0 = time.time()

            print ("111111+++++++++++++++++++++++++++++++++++++")

            chunks_added = pipeline["add_document"](file_paths = [file_path],
                                                    chunk_size = chunk_size,
                                                    chunk_overlap = chunk_overlap)

            print ("2222222222s+++++++++++++++++++++++++++++++++++++")
            t1 = time.time()

            process_ms = int((t1 - t0) * 1000)

            print (f"---------------> 处理时间: {process_ms}ms")

            if chunks_added == 0:
                return f"未能从文件解析内容: {os.path.basename(file_path)}"

            return (f"文档已添加到知识库: {os.path.basename(file_path)} \n"
                    f"分块数量: {chunks_added} \n"
                    f"处理时间: {process_ms} ms\n"
                    f"命名空间: {pipeline.get('namespace', self.rag_namespace)}")

        except Exception as e:
            return f"添加文档失败: {str(e)}"
    
    @tool_action("rag_add_text", "添加文本内容") 
    def _add_text(self, text: str, 
                document_id: str = None,
                namespace: str = "default",
                chunk_size: int = 800,
                chunk_overlap: int = 100):

        metadata = None 

        try:
            if not text or not text.strip():
                return "文本内容为空"

            document_id = document_id or f"text_{abs(hash(text)) % 100000}"

            tmp_path = os.path.join(self.knowledge_base_path, f"{document_id}.md")

            try:
                with open(tmp_path, 'w+', encoding='utf-8') as fw:
                    fw.write(text)

                pipeline = self.get_pipeline(namespace)

                t0 = time.time()

                chunks_added = pipeline["add_text"](file_paths=[tmp_path], 
                                                    chunk_size=chunk_size,
                                                    chunk_overlap=chunk_overlap)
                t1 = time.time()

                process_ms = int((t1 - t0) * 1000)

                if chunks_added == 0:
                    return f"未能从文本生成有效分块"
                
                return (f"文本已添加到知识库: {os.path.basename(tmp_path)} \n"
                    f"分块数量: {chunks_added} \n"
                    f"处理时间: {process_ms} ms\n"
                    f"命名空间: {pipeline.get('namespace', self.rag_namespace)}") 

            
            finally:
                try:
                    if os.path.exist(tmp_path):
                        os.remove(tmp_path)
                except Exception as e:
                    pass
        except Exception as e:
            return f"添加文本失败: {str(e)}"

    @tool_action("rag_search", "搜索知识库中的相关内容")
    def _search(self, query:str, 
                limit: int = 5,
                min_score: float = 0.1,
                enable_advanced_search: bool = True,
                max_chars: int = 1200,
                include_citations: bool = True,
                namespace: str = "default"):
        try:
            if not query or not query.strip():
                return "搜索不能为空"

            pipeline = self.get_pipeline(namespace)

            if enable_advanced_search:
                results = pipeline["search_advanced"](
                    query = query,
                    top_k = limit,
                    enable_mqe = True,
                    enable_hyde = True,
                    score_threshold=min_score if min_score > 0 else None)
            else:
                results = pipeline["search"](query = query,
                                            top_k = limit,
                                            score_threshold = min_score if min_score > 0 else None)
            if not results:
                return f"未找到与{query}相关内容"

            search_result = ["搜索结果:"]

            for i, result in enumerate(results, 1):
                meta = result.get("metadata", {})
                score = result.get("score", 0.0)
                content = meta.get("content", "")[:200] + "..."
                source = meta.get("search_path", "unknown")


                def clean_text(text):
                    try:
                        return str(text).encode('utf-8', errors='ignore').decode('utf-8')
                    except Exception as e:
                        return str(text)

                clean_content = clean_text(content)
                clean_source = clean_text(source)

                search_result.append(f"\n{i}. 文档: **{clean_source}** (相似度: {score: .3f})")
                search_result.append(f" {clean_content}")

                if include_citations and meta.get("heading_path"):
                    clean_heading = clean_text(str(meta['heading_path']))
                    search_result.append(f" 章节: {clean_heading}")

            return "\n".jion(search_result)

        except Exception as e:
            return f"搜索失败: {str(e)}"

    @tool_action("rag_ask", "基于知识库进行智能问答")
    def _ask(self, 
            question: str,
            limit: int = 5,
            enable_advanced_search: bool = True,
            include_citations: bool = True,
            max_chars: int = 1200,
            namespace: str = "default"):

        try:
           
            if not question or not question.strip():
                return "请提供必要的查询"

            user_question = question.strip()

            print (f"智能问答------->: {user_question}")

            pipeline = self.get_pipeline(namespace)
            
            print (f"----->RAG管道: {pipeline.get('namespace', self.rag_namespace)}")

            search_start = time.time()

            if enable_advanced_search:
                results = pipeline["search_advanced"](
                                        query = user_question,
                                        top_k = limit,
                                        enable_mqe = True,
                                        enable_hyde = True,
                                        )

                print (f"高级搜索结果: {results}")
            else:
                results = pipeline["search"](query = user_question,
                                            top_k = limit)

            search_time = int((time.time() - search_start) * 1000)

            if not results:
                return (f"抱歉: 我在知识库没有找到与{user_question}相关信息。\n\n"
                    f"建议: \n"
                    f"尝试使用更简洁的关键词\n"
                    f"检查是否已添加相关文档\n"
                    f"使用stats 操作查看知识库状态")

            context_parts = []
            citations = []
            total_score = 0

            for i, result in enumerate(results, 1):
                meta = result.get("metadata", {})
                content = meta.get("content", "").strip()
                source = meta.get("search_path", "unknown")
                score = result.get("score", 0.0)
                total_score += score

                if content:
                    cleaned_content = self._clean_content_for_context(content)

                    context_parts.append(f"片段 {i + 1} : {cleaned_content}")

                    if include_citations:
                        citations.append({"index": i + 1, "source" : os.path.basename(source), "score":score})

            # 3、构建上下文（智能截断）
            context = "\n\n".join(context_parts)
            if len(context) > max_chars:
                context = self._smart_truncate_context(context, max_chars)
            
            # 4、构建增强提示词
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(question, context)

            messages = [{"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}]
            
            # 5、调用 LLM 生成答案
            llm_start = time.time()

            answer = self.llm.invoke(messages)

            llm_time = int((time.time() - llm_start) * 1000)

            if not answer or not answer.strip():
                return "LLM 未能生成有效答案，请稍后重试"

            # 6、构建最终答案

            final_answer = self._format_final_answer(
                                            question = user_question,
                                            answer = answer.strip(),
                                            citations = citations if include_citations else None,
                                            search_time = search_time,
                                            llm_time = llm_time,
                                            avg_score = total_score / len(results) if results else 0
                                            )

            return final_answer

        except Exception as e:
            return f"智能回答失败: {str(e)}"


    def _format_final_answer(self, question: str, answer: str,
                            citations:Optional[List[Dict]] = None,
                            search_time: int = 0,
                            llm_time: int = 0,
                            avg_score: float = 0):

        result = ["** 智能问答结果 **\n"]
        result.append(answer)

        if citations:
            result.append("\n\n ** 参考来源 ** \n")

            for citation in citations:
                score_emoji = "🟢" if citation["score"] > 0.8 else "🟡" if citation["score"] > 0.6 else "🔵"
                result.append(f"{score_emoji} [{citation['index']}] {citation['source']} (相似度: {citation['score']:.3f})")
        result.append(f"\n检索: {search_time}ms | 生成: {llm_time}ms | 平均时间: {avg_score: .3f}")

        return "\n".join(result)
    
    def _clean_content_for_context(self, content: str):
        """清理内容用于上下文"""

        content = " ".join(content.split())
        if len(content) > 300:
            content = content[:300] + "...."
        return content

    def _smart_truncate_context(self, context:str, max_chars: int):
        """智能截断上下文，保持段落完整性"""

        if len(context) <= max_chars:
            return context

        truncated = context[:max_chars]

        last_break = truncated.rfind("\n\n")

        if last_break > max_chars * 0.7:
            return truncated[:last_break] + "\n\n[...更多内容被截断]"
        else:
            return truncated[:max_chars - 20] + "...[内容被截断]"

    def _build_system_prompt(self):
        """构建系统提示词"""

        return (
            "你是一个专业的知识助手，具备以下能力：\n"
            "1. 📖 精准理解：仔细理解用户问题的核心意图\n"
            "2. 🎯 可信回答：严格基于提供的上下文信息回答，不编造内容\n"
            "3. 🔍 信息整合：从多个片段中提取关键信息，形成完整答案\n"
            "4. 💡 清晰表达：用简洁明了的语言回答，适当使用结构化格式\n"
            "5. 🚫 诚实表达：如果上下文不足以回答问题，请坦诚说明\n\n"
            "回答格式要求：\n"
            "• 直接回答核心问题\n"
            "• 必要时使用要点或步骤\n"
            "• 引用关键原文时使用引号\n"
            "• 避免重复和冗余"
            )

    def _build_user_prompt(self, question: str, context: str):
        """构建用户提示词"""

        return (
            f"请基于以下上下文信息回答问题：\n\n"
            f"【问题】{question}\n\n"
            f"【相关上下文】\n{context}\n\n"
            f"【要求】请提供准确、有帮助的回答。如果上下文信息不足，请说明需要什么额外信息。"
            )
    
    @tool_action("rag_clear", "清空知识库 (危险操作，请谨慎使用)")
    def _clear_knowledge_base(self, confirm: bool = False, namespace: str = "default"):

        try:
            if not confirm:
                return ("危险操作: 清空知识库将删除所有数据! \n"
                    "请使用 confirm = true 参数确认执行。")

            pipeline = self.get_pipeline(namespace)
            store = pipeline.get("store")

            namespace_id = pipeline.get("namespace", self.rag_namespace)
            success = store.clear_collection() if store else False

            if success:
                self._pipelines[namespace_id] = create_rag_pipeline(
                                                            qdrant_url = self.qdrant_url,
                                                            qdrant_api_key = self.qdrant_api_key,
                                                            collection_name = self.collection_name,
                                                            rag_namespace = namespace_id)
                return f"知识库已成功清空: (命名空间: {namespace_id})"
            else:
                return "清空知识库失败"
        except Exception as e:
            return f"清空知识库失败: {str(e)}"


    @tool_action("rag_stats", "获取知识库统计信息")
    def _get_stats(self, namespace : str = "default"):

        try:
            pipeline = self.get_pipeline(namespace)

            stats = pipeline["get_stats"]()

            stats_info = ["** RAG 知识库统计 **", 
                        f"命名空间: {pipeline.get('namespace', self.rag_namespace)}",
                        f"集合名称: {self.collection_name}",
                        f"存储根路径: {self.knowledge_base_path}"]

            if stats:
                store_type = stats.get("store_type", "unknown")

                total_vectors = (
                                stats.get("points_count") or 
                                stats.get("vectors_count") or 
                                stats.get("count") or 0
                                )
                
                stats.extend([
                            f"存储类型: {store_type}",
                            f"文档分块数: {int(total_vectors)}"
                            ])
                
                if "config" in stats:
                    config = stats["config"]

                    if isinstance(config, dict):
                        vector_size = config.get("vector_size", "unknown")
                        distance = config.get("distance", "unknown")

                        stats_info.extend([f"向量维度: {vector_size}", f"距离度量: {distance}"])

            stats_info.extend(["", "** 系统状态 **", 
                            f"RAG 管道: {'正常' if self.initialized else '异常'}",
                            f"LLM 连接: {'正常' if hasattr(self, 'llm') else '异常'}"])
            
            return "\n".join(stats_info)
        except Exception as e:
            return f"获取统计信息失败: {str(e)}"

    def get_relevant_context(self, query: str, 
                            limit: int = 3, max_chars: int = 1200,
                            namespace: Optional[str] = None):

        try:
            if not query:
                return ""

            pipeline = self.get_pipeline(namespace)

            results = pipeline["search"](query = query, top_k = limit)

            if not results:
                return ""

            context_parts = []

            for result in results:
                content = result.get("metadata", {}).get("content", "")
                if content:
                    context_parts.append(content)

            merged_context = "\n\n".join(context_parts)

            if len(merged_context) > max_chars:
                merged_context = merged_context[:max_chars] + '...'

            return merged_context
            
        except Exception as e:
            return f"获取上下文失败: {str(e)}"

    def batch_add_texts(self, texts: List[str], document_ids: Optional[List[str]] = None,
                        chunk_size: int = 800, chunk_overlap: int = 800,
                        namespace: Optional[str] = None):

        """批量添加文本"""

        try:
            if not texts:
                return "文本列表不能为空"

            if document_ids and len(document_ids) != len(texts):
                return "文本数量和文档ID不匹配"

            pipeline = self.get_pipeline(namespace)

            t0 = time.time()

            total_chunks = 0

            successful_files = []

            for i, text in enumerate(texts):
                if not text or not text.strip():
                    continue

                doc_id = document_ids[i] if document_ids else f"bacth_text_{i}"

                tmp_path = os.path.join(self.knowledge_base_path, doc_id)

                try:
                    with open(tmp_path, "w+") as fw:
                        fw.write(text)

                    chunks_added = pipeline["add_documents"](
                                                    file_paths = [tmp_path],
                                                    chunk_size = chunk_size,
                                                    chunk_overlap = chunk_overlap)
                    total_chunks += chunks_added
                    successful_files.append(doc_id)
                finally:
                    try:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)
                    except Exception as e:
                        pass

            t1 = time.time()

            process_ms = int((t1 - t0) * 1000)

            return (f"批量添加完成\n"
                    f"成功文件: {len(successful_files)} / {len(texts)}"
                    f"总分块数: {tool_chunks}\n"
                    f"处理时间: {process_ms}ms\n")
        except Exception as e:
            return f"批量添加失败: {str(e)}"

    def clear_all_namespaces(self):
        """清空当前工具管理的所有命名空间数据"""

        try:
            for ns, pipeline in self._pipelines.items():
                store = pipeline.get("store")
                if store:
                    store.clear_collection()
            self._pipelines.clear()
            self._init_components()
            return "所有命名空间已清空并已重新初始化"
        except Exception as e:
            return f"清空所有命名空间失败: {str(e)}"

    def add_document(self, file_path: str, namespace: str = "default"):
        """添加单个文档"""
        return self.run({
                        "action":"add_document",
                        "file_path": file_path,
                        "namespace": namespace})

    def add_text(self, text: str, namespace: str = "default", document_id: str = None):
        """添加单个文本内容"""
        return self.run({
                        "action": "add_text",
                        "text": text,
                        "namespace": namespace,
                        "document_id": document_id
            })

    def ask(self, question: str, namespace: str = "default", **kwargs):
        """便捷方法：智能问答"""

        params = {"action": "ask", "question": question, "namespace": namespace}

        params.update(kwargs)
        return self.run(params)

    def search(self, query: str, namespace: str = "default", **kwargs):
        """便捷方法：智能搜索"""

        params = {"action": "ask", "query": query, "namespace": namespace}
        params.update(kwargs)
        return self.run(params)

    def add_documents_bacth(self, file_paths:List[str], namespace: str = "default"):
        """批量添加多个文档"""

        if not file_paths:
            return "文件列表不能为空"

        results = []
        successful = 0

        failed = 0
        total_chunks = 0

        start_time = time.time()

        for i, file_path in enumerate(file_paths, 1):
            print (f"处理文档{i}/{len(file_paths)}: {os.path.basename(file_path)}")

            try:
                result = self.add_document(file_path, namespace)
                if "文档已添加到知识库" in result:
                    successful += 1
                    
                    if "分块数量:" in result:
                        chunks = int(result.split("分块数量:")[1].strip().split('\n')[0])
                        total_chunks += chunks
                else:
                    failed += 1
                    results.append(f"{os.path.basename(file_path)}: 处理失败")
            except Exception as e:
                failed += 1
                results.append(f"{os.path.basename(file_path)}: {str(e)}")

        process_time = int((time.time() - start_time) * 1000)

        summary = ["***批量处理完成***", 
                    f"成功: {successful} / {len(file_paths)} 个文档",
                    f"总分块数: {total_chunks}",
                    f"总耗时: {process_time} ms",
                    f"命名空间:{namespace}"]

        if failed > 0:
            summary.append(f"失败{failed}个文档")
            summary.append("\n失败详情:**")
            summary.extend(results)

        return "\n".join(summary)

    
    def add_texts_bacth(self, texts:List[str], namespace: str = "default", document_ids: Optional[List[str]] = None):
        """批量添加多个文本"""

        if not texts:
            return "文本列表不能为空"

        if document_ids and len(document_ids) != len(texts):
            return "文本数量与文档ID数量不匹配"

        results = []
        successful = 0

        failed = 0
        total_chunks = 0

        start_time = time.time()

        for i, text in enumerate(texts):
            doc_id = document_ids[i] if document_ids else f"bacth_text_{i + 1}"
            print (f"处理文本{i + 1}/{len(texts)}: {doc_id}")

            try:
                result = self.add_text(text, namespace, doc_id)
                if "文本已添加到知识库" in result:
                    successful += 1
                    
                    if "分块数量:" in result:
                        chunks = int(result.split("分块数量:")[1].strip().split('\n')[0])
                        total_chunks += chunks
                else:
                    failed += 1
                    results.append(f"{doc_id}: 处理失败")
            except Exception as e:
                failed += 1
                results.append(f"{doc_id}: {str(e)}")

        process_time = int((time.time() - start_time) * 1000)

        summary = ["***批量处理完成***", 
                    f"成功: {successful} / {len(texts)} 个文本",
                    f"总分块数: {total_chunks}",
                    f"总耗时: {process_time} ms",
                    f"命名空间:{namespace}"]

        if failed > 0:
            summary.append(f"失败{failed}个文本")
            summary.append("\n失败详情:**")
            summary.extend(results)

        return "\n".join(summary)













    



        

        
