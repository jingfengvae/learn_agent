"""
基于 agent-connect 库的 ANP 协议实现

使用 agent-connect 库实现 Agent NetWork Protocol 功能

注意：agent-connect 是一个底层的网络协议库，提供加密和认证功能

这里创建一个简化的包装器，使其易于使用
"""

from typing import Dict, List, Any, Optional
import asyncio
import json

class ServiceInfo:
    """服务信息"""

    def __init__(
            self,
            service_id: str,
            service_type: str,
            endpoint: str,
            service_name: Optional[str] = None,
            capabilities: Optional[List[str]] = None,
            metadata: Optional[Dict[str, Any]] = None):

        self.service_id = service_id
        self.service_type = service_type
        self.endpoint = endpoint
        self.service_name = service_name or service_id
        self.capabilities = capabilities or []
        self.metadata = metadata or {}

    def to_dict(self):
        """转化为字典"""

        return {
            "service_id": self.service_id,
            "service_type": self.service_type,
            "endpoint": self.endpoint,
            "service_name": self.service_name,
            "capablities": self.capabilities,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data:Dict[str, Any]):
        """从字典中创建"""
        return cls(
            service_id = data['service_id'], 
            service_type = data['service_type'],
            endpoint = data['endpoint'],
            service_name = data.get('service_name'),
            capabilities = data.get('capabilities'),
            metadata = data.get('metadata', {})
        )


class ANPDicovery:
    """基于 Agent-Connect 的服务发现"""

    def __init__(self):
        """初始化服务发现"""
        self._services: Dict[str, ServiceInfo] = {}

    def register_service(self, service:ServiceInfo):
        """
        注册服务
        
        Args:
            service: 服务信息
        Return:
            是否注册成功
        """

        self._services[service.service_id] = service

        return True

    def unregister_service(self, service_id):
        """
        注销服务
        
        Args:
            service_id: 服务ID
        
        Return:
            是否注销成功
        """

        if service_id in self._services:
            del self._services[service_id]
            return True
        return False

    def discover_services(
                    self,
                    service_type: Optional[str] = None,
                    filters: Optional[Dict[str, Any]] = None
                    ):
        """
        发现服务
        Args:
            service_type: 服务类型
            filters: 过滤条件

        Return：
            可用的服务列表
        """

        services = list(self._services.values())

        # 按类型过滤：
        if service_type:
            services = [service for service in services if service.service_type == service_type]

        # 按元数据过滤
        if filters:
            def matchs_filters(service: ServiceInfo):
                for key, val in filters.items():
                    if service.metadata.get(key) != val:
                        return False
                return True

            services = [service for service in services if matchs_filters(service)]

        return services

    def get_service(self, server_id):
        """
        获取服务信息

        Args: 
            server_id: 服务ID

        Return:

            Service 信息，不存在返回空
        """

        if server_id not in self._services:
            return None
        
        return self._services[server_id]

    def list_all_services(self):
        """列出所有服务"""
        return list(self._services.values())


class ANPNetWork:
    """
    基于 Agent-Connect 的网络管理实现
    """

    def __init__(self, network_id: str = "default"):
        """
        初始化网络管理器

        Args:
           network_id: 网络ID
        """
        self.network_id = network_id
        self._nodes: Dict[str, Dict[str, Any]] = {}
        self._connections: Dict[str, List[str]] = {}

    def add_node(self, node_id: str, endpoint: str, metadata: Optional[Dict[str, Any]] = None):
        """
        添加节点到网络

        Args:
            node_id: 节点ID
            endpoint: 节点端点
            metadata: 节点元数据
        """

        self._nodes[node_id] = {
            "note_id": node_id,
            "endpoint": endpoint,
            "metadata": metadata,
            "status": "active"
        }

        self._connections[node_id] = []
    
    def remove_node(self, node_id: str):
        """
        从网络中移除节点

        Args:
           node_id: 节点ID
        
        Return:
            是否移除成功
        """
        if node_id in self._nodes:
            del self._nodes[node_id]
            del self._connections[node_id]
            # 移除其他节点到此节点的连接
            for connections in self._connections.values():
                if node_id in connections:
                    connections.remove(node_id)
            return True
        return False

    def connect_nodes(self, from_node_id: str, to_node_id: str):
        """
        连接2个节点

        Args:
           from_node_id: 源节点ID
           to_node_id: 目标节点ID
        """

        if from_node_id in self._connections and to_node_id in self._nodes:
            if to_node_id not in self._connections[from_node_id]:
                self._connections[from_node_id].append(to_node_id)

    def route_message(
                self,
                from_node_id: str,
                to_node_id: str,
                message: Dict[str, Any]
                ):
        """
        路由消息（简单的直接路由）

        Args:
            from_node_id: 源节点 ID
            to_node_id: 目标节点 ID
            message: 消息内容
        Return:
            路由路径，如果没有路由返回空
        """

        if from_node_id not in self._nodes or to_node_id not in self._nodes:
            return None

        # 简单实现，直接路由
        if to_node_id in self._connections[from_node_id]:
            return [from_node_id, to_node_id]

        # 尝试通过一跳中转
        for intermediate in self._connections[from_node_id]:
            if to_node_id in self._connections[intermediate]:
                return [from_node_id, intermediate, to_node_id]

        return None


    def broadcast_message(self, from_node_id: str, message: Dict[str, Any]):
        """
        广播消息到所有连接到的节点

        Args
            from_node_id: 源节点ID
            message: 广播的消息
        
        Return:
            接收消息的节点列表
        """

        if from_node_id in self._connections:
            return self._connections[from_node_id].copy()

        return []


    def get_network_stats(self):
        """
        获取网络信息
        """
        total_connections = sum(len(conns) for conns in self._connections.values())
        active_nodes = sum(1 for node in self._nodes.values() if node['status'] == "active")

        return {
            "network_id": self.network_id,
            "total_nodes": len(self._nodes),
            "active_nodes": active_nodes,
            "total_connections": total_connections,
            "nodes": list(self._nodes.keys())
        }

    def get_node_info(self, node_id: str):
        """
        获取节点信息
        """
        if node_id not in self._nodes:
            return None

        node_info = self._nodes[node_id]
        node_info["connections"] = self._connections[node_id].copy()
        return node_info

# 创建一个简单的 ANP 网络
def create_example_network():
    """创建一个示例ANP网络"""

    network = ANPNetWork(network_id = "network_example")

    # 添加节点
    network.add_node("node1", "http://localhost:8001", {"type": "agent", "role": "coordinator"})
    network.add_node("node2", "http://localhost:8002", {"type": "agent", "role": "worker"})
    network.add_node("node3", "http://localhost:8003", {"type": "agent", "role": "worker"})

    # 连接节点
    network.connect_nodes("node1", "node2")
    network.connect_nodes("node1", "node3")
    network.connect_nodes("node2", "node3")

    return network

if __name__ == "__main__":
    print ("创建示例ANP网络...")
    network = create_example_network()

    print (f"ANP NetWork: {network.network_id}")
    print (f"NetWork Stats: ")
    stats = network.get_network_stats()
    print (stats)
    print ("\n")

    print ("测试路由...")
    path = network.route_message("node1", "node2", {"type": "test", "content": "Hello"})
    print (f"Route from node1 to node2: {'--->'.join(path) if path else 'No route found....'}") 

    path = network.route_message("node3", "node2", {"type": "test", "content": "Hello"})
    print (f"Route from node3 to node2: {'--->'.join(path) if path else 'No route found....'}") 

    print (f"测试广播...")
    recipients = network.broadcast_message("node1", {"type": "broadcast", "content": "Hello everyone..."})
    print (f"Broadcast from node1 to: {', '.join(recipients)}")   

    print (f"*****" * 20)
    print ("创建服务发现。。。。")

    discovery = ANPDicovery()

    service1 = ServiceInfo(
            service_id = "nlp_agent_1",
            service_type = "nlp",
            endpoint = "http://localhost:8001",
            service_name = "NLP处理专家A",
            capabilities = ["text_analysis", "sentiment_analysis", "ner"],
            metadata = {"load": 0.3, "price": 0.01, "version": "1.0.0"}
    )        

    discovery.register_service(service1)

    service2 = ServiceInfo(
            service_id = "nlp_agent_2",
            service_type = "nlp",
            endpoint = "http://localhost:8002",
            service_name = "NLP处理专家B",
            capabilities = ["text_analysis", "sentiment_analysis"],
            metadata = {"load": 0.7, "price": 0.02, "version": "1.1.0"}
        )   

    discovery.register_service(service2)

    print ("服务已注册。。。。")
                

    # 按类型查找服务
    nlp_services = discovery.discover_services(service_type = "nlp")
    print (f"找到{len(nlp_services)}个 NLP 服务。。。")

    # 选择负载最低的服务
    best_service = min(nlp_services, key = lambda s: s.metadata.get('load', 1.0))
    print (f"最佳服务: {best_service.service_name} : {best_service.metadata.get('load')}")

    # 创建网络
    network = ANPNetWork(network_id = "ai_cluster")

    # 添加节点
    for service in discovery.list_all_services():
        network.add_node(service.service_id, service.endpoint, service.metadata)

    # 建立连接
    network.connect_nodes(service1.service_id, service2.service_id)

    stats = network.get_network_stats()

    print (f"网络构建完成，节点信息: {stats}")
