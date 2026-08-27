"""
ANP协议工具

- ANP Tool： 基于概念实现，用于服务发现和网络管理
"""

from typing import Dict, List, Any, Optional
from tool_base import Tool, ToolParameter
from anp_network import ANPDicovery, ANPNetWork, ServiceInfo
import os


class ANPTool(Tool):
    """
    ANP 工具
    提供Agent网络管理功能，包括服务发现、节点管理、消息路由
    """

    def __init__(
                self, 
                name: str = "anp", 
                description: str = None, 
                discovery = None,
                network = None):
        """
        Args:
            name: 工具名称
            description: 工具描述
            discovery: 可选的 ANPDiscovery服务发现实例，如果不提供则创建
            network: 可选的 ANPNetWork 实例，如果不提供则创建
        """
        
        if description == None:
            description = "Agent网络管理工具，支持服务发现、节点管理和消息路由。概念性实现。"
        
        super().__init__(name = name, description = description)

        self._discovery = discovery if discovery is not None else ANPDicovery()
        self._network = network if network is not None else ANPNetWork()

    def run(self, parameters: Dict[str, Any]):
        """
        执行 ANP 操作

        Args:
            parameters
            - action: 操作类型（register_service, discover_services, add_node, route_message, get_stats）
            - service_id, service_type, endpoint: 服务信息
            - from_node, to_node, message: 路由信息
        Return：
            操作结果
        """

        action = parameters.get('action', '').lower()

        if not action:
            return "Error: 必须指定 action 参数"

        try:
            if action == "register_service":
                service_id = parameters.get('service_id')
                service_type = parameters.get('service_type')
                endpoint = parameters.get('endpoint')
                metadata = parameters.get('metadata', {})
                service_name = parameters.get('service_name')
                capabilities = parameters.get('capablities', [])

                if not all([service_id, service_type, endpoint]):
                    return "Error: 必须指定参数（service_id, service_type, endpoint）"

                service = ServiceInfo(
                                    service_id, 
                                    service_type, 
                                    endpoint, 
                                    service_name,
                                    capabilities,
                                    metadata
                                    )
                self._discovery.register_service(service)
                return f"已注册服务: {service_id}"

            elif action == "unregister_service":
                service_id = parameters.get('service_id', '')
                if not service_id:
                    return "Error: 必须指定参数（service_id）"

                success = self._discovery.unregister_service(service_id)

                if success:
                    return f"已注销服务: {service_id}"
                else:
                    return f"Error: {service_id} 不存在"
            
            elif action == "discover_services":
                service_type = parameters.get('service_type')
                services = self._discovery.discover_services(service_type)

                if not services:
                    return "没有找到相关服务..."
                
                result = f"找到{len(services)}个服务:\n"
                for service in services:
                    result += f"服务ID: {service.service_id}\n"
                    result += f"  名称: {service.service_name}\n"
                    result += f"  类型: {service.service_type}\n"
                    result += f"  端点: {service.endpoint}\n"
                    if service.capabilities:
                        result += f"  能力:{','.join(service.capabilities)}\n"

                    if service.metadata:
                        result += f"  元数据: {service.metadata}\n"
                return result

            elif action == "get_service":
                service_id = parameters.get('service_id')
                if not service_id:
                    return "Error: 必须指定参数（service_id）"

                service = self._discovery.get_service(service_id)

                if service is None:
                    return f"服务不存在: {service_id}"

                result = f"{service_id}的信息如下:\n"
                result += f"服务ID: {service.service_id}\n"
                result += f"  名称: {service.service_name}\n"
                result += f"  类型: {service.service_type}\n"
                result += f"  端点: {service.endpoint}\n"
                if service.capabilities:
                    result += f"  能力:{','.join(service.capabilities)}\n"
                
                if service.metadata:
                    result += f"  元数据: {service.metadata}\n"
                return result

            elif action == "add_node":
                node_id = parameters.get("node_id")
                endpoint = parameters.get("endpoint")
                metadata = parameters.get("metadata", {})
                
                if not all([node_id, endpoint]):
                    return "错误：必须指定 node_id 和 endpoint 参数"
                
                self._network.add_node(node_id, endpoint, metadata)
                return f"已添加节点 '{node_id}'"

            elif action == "route_message":
                from_node_id = parameters.get('from_node_id')
                to_node_id = parameters.get('to_node_id')
                message = parameters.get('message', {})

                if not all([from_node_id, to_node_id]):
                    return "Error: 必须指定参数 （from_node_id,to_node_id）"
                
                paths = self._network.route_message(from_node_id, to_node_id)
                
                if paths:
                    return f"消息路由路径: {', '.join(paths)}"
                else:
                    return "无法找到路由路径..."

            elif action == "get_stats":
                stats = self._network.get_network_stats()
                result = "网络统计:\n"
                for key, value in stats.items():
                    result += f"- {key}: {value}\n"
                return result

            else:
                return f"不支持的操作: {action}"
        except Exception as e:
            print (f"ANP 操作失败: {e}")
            return (f"ANP 操作失败: {e}")

    def get_parameters(self):
        """获取工具参数定义"""
        
        return [
            ToolParameter(
                name = "action",
                type = "string",
                description = "操作类型: register_service, unregister_service, discover_services, get_service, add_node, route_message, get_stats",
                required = True
            ),
            ToolParameter(
                name = "service_id",
                type = "string",
                description = "服务ID: (register_service, unregister_service, get_service)操作需要",
                required = False
            ),
            ToolParameter(
                name = "endpoint",
                type = "string",
                description = "服务端点地址: (register_service， add_node)操作需要",
                required = False
            ),
            ToolParameter(
                name="service_type",
                type="string",
                description = "服务类型（register_service）操作需要",
                required=False
            ),
            ToolParameter(
                name = "node_id",
                type = "string",
                description = "节点ID: (add_node)操作需要",
                required = False
            ),
            ToolParameter(
                name = "from_node_id",
                type = "string",
                description = "源节点ID: (route_message)操作需要",
                required = False
            ),
            ToolParameter(
                name = "to_node_id",
                type = "string",
                description = "目标节点ID: (route_message)操作需要",
                required = False
            ),
            ToolParameter(
                name = "message",
                type = "object",
                description = "消息内容: (route_message)操作需要",
                required = False
            ),
            ToolParameter(
                name = "metadata",
                type = "object",
                description = "元数据内容: (register_service, add_node)操作可选",
                required = False
            )
        ]







        
