from tool_base import Tool

from typing import Dict, Any, List

import ast
import operator
import math

class CalculatorTool(Tool):
    """docstring for Calculator"""
    
    def run(self, parameters: Dict[str, Any]):
        
        if not parameters or 'expression' not in parameters:
            return "没有需要计算的表达式！"

        expression = parameters['expression'].strip()

        if not expression:
            return "计算表达式不能为空"

        # 支持的基本运算
        operators = {
            ast.Add: operator.add,      # +
            ast.Sub: operator.sub,      # -
            ast.Mult: operator.mul,     # *
            ast.Div: operator.truediv,  # /
        }
    
        # 支持的基本函数
        functions = {
            'sqrt': math.sqrt,
            'pi': math.pi,
        }
    
        try:
            node = ast.parse(expression, mode='eval')
            result = self._eval_node(node.body, operators, functions)
            return str(result)
        except:
            return "计算失败，请检查表达式格式"

    def _eval_node(self, node, operators, functions):
        """简化的表达式求值"""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            left = _eval_node(node.left, operators, functions)
            right = _eval_node(node.right, operators, functions)
            op = operators.get(type(node.op))
            return op(left, right)
        elif isinstance(node, ast.Call):
            func_name = node.func.id
            if func_name in functions:
                args = [_eval_node(arg, operators, functions) for arg in node.args]
                return functions[func_name](*args)
        elif isinstance(node, ast.Name):
            if node.id in functions:
                return functions[node.id]

    def get_parameters(self):
        tool_params = []
        cal_tool_params = ToolParameter(self.name, "str", self.description)
        tool_params.append(cal_tool_params)
        return tool_params


