"""
基于官方 a2a-sdk 库实现 A2A 协议
"""

from typing import List, Any, Dict, Optional
import asyncio

from flask import Flask, request, jsonify

class A2AServer:
    """
    A2A 服务器 
    """

    def __init__(
            self,
            name:str,
            description: str,
            version: str = "1.0.0",
            capabilities: Optional[Dict[str, Any]] = None):

        """
        初始化 A2A Server

        Args:
            name: Agent 名称
            description: Agent 描述
            version: Agent 版本
            capabilities: Agent 能力描述
        """
        self.name = name
        self.description = description
        self.version = version
        self.capabilities = capabilities or {}
        self.skills = {}

    def add_skill(self, skill_name: str, func):
        """
        添加技能到服务器
        """
        self.skills[skill_name] = func
        return func

    def skill(self, skill_name: str):
        """
        装饰器方式添加技能
        """

        def decorator(func):
            return self.add_skill(skill_name, func)
        return decorator

    def run(self, host: str = "0.0.0.0", port: int = 5000):
        """
        运行服务器（使用 Flask 提供 HTTP API）
        """

        app = Flask(self.name)

        # 禁用 Falsk 的日志输出
        import  logging

        log = logging.getLogger("werkzeug")
        log.setLevel(logging.ERROR)

        @app.route('/info', methods = ['GET'])
        def get_info():
            """
            获取 Agent 信息
            """
            return jsonify(self.get_info())

        @app.route('/skills', methods=['GET'])
        def list_skills():
            """
            列出所有技能
            """
            return jsonify({
                "skills": list(self.skills.keys()),
                "count": len(self.skills)
            })

        @app.route('/execute/<skill_name>', methods=['POST'])
        def execute_skill(skill_name):
            """
            执行指定技能
            """
            if skill_name not in self.skills:
                return jsonify({
                    "error": f"Skill '{skill_name}' not found",
                    "available_skills": list(self.skills.keys())
                }), 404

            try:
                data = request.get_json() or {}
                text = data.get('text', data.get('query', ''))

                # 调用技能函数
                result = self.skills[skill_name](text)

                return jsonify({
                    "skill": skill_name,
                    "result": result,
                    "status": "success"
                })
            except Exception as e:
                return jsonify({
                    "error": str(e),
                    "skill": skill_name,
                    "status": "error"
                }), 500

        @app.route('/ask', methods=['POST'])
        def ask():
            """
            通用问答接口(自动选择技能)
            """
            try:
                data = request.get_json() or {}
                question = data.get('question', data.get('text', ''))

                # 简单策略： 尝试所有技能，返回第一个非错误结果
                for skill_name, skill_func in self.skills.items():
                    try:
                        result = skill_func(question)
                        if result and not result.startswith("Error"):
                            return jsonify({
                                "answer": result,
                                "skill_used": skill_name,
                                "status": "success"
                            })
                    except Exception as e:
                        continue
                return jsonify({
                    "answer": "No suitable skill found for this question",
                    "status": "no match"
                })
            except Exception as e:
                return jsonify({
                    "error": str(e),
                    "status": "error"
                }), 500

        @app.route('/health', methods=['GET'])
        def health():
            """健康检查"""
            return jsonify({
                "status":"healthy",
                "agent": self.name
            })

        # 启动服务器
        print (f"A2A 服务器{self.name} 启动在{host}:{port}")
        print (f"描述: {self.description}....")
        print (f"可用技能：{len(self.skills.keys())}")
        print (f"API 端点：")
        print(f"   - GET  {host}:{port}/info - 获取 Agent 信息")
        print(f"   - GET  {host}:{port}/skills - 列出技能")
        print(f"   - POST {host}:{port}/execute/<skill> - 执行技能")
        print(f"   - POST {host}:{port}/ask - 通用问答")
        print(f"   - GET  {host}:{port}/health - 健康检查")
        print()

        app.run(host = host, port = port, debug = False)

    def get_info(self):
        """获取服务器信息"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "capabilities": self.capabilities,
            "protocol": "A2A",
            "skills": list(self.skills.keys())
        }

        
       