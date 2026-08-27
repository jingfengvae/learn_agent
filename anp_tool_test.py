from anp_network import ANPDicovery, ANPNetWork, ServiceInfo
from hello_agent import HelloAgentsLLM
from simple_agent import SimpleAgent
import random
from anp_tool import ANPTool
from dotenv import load_dotenv

load_dotenv()

llm = HelloAgentsLLM()

# 1、创建服务发现中心
discovery = ANPDicovery()

#2、注册多个计算节点
for i in range(10):
    service = ServiceInfo(
                service_id = f"compute_node_{i}",
                service_type = "compute",
                endpoint = f"http://node{i}:8000",
                service_name = f"计算节点{i}",
                capabilities = ["data_processing", "ml_training"],
                metadata = {
                        "load": random.uniform(0.1, 0.9),
                        "cpu_cores": random.choice([4, 8, 16]),
                        "memory_db": random.choice([16, 32, 64]),
                        "gpu": random.choice([True, False])
                    }
                )
    discovery.register_service(service)

print (f"已注册了{len(discovery.list_all_services())}个节点")

#3、创建任务调度Agent
scheduler = SimpleAgent(
                name = "任务调度器",
                llm = llm,
                system_prompt = """
                            你是一个智能任务调度器，负责:
                            1、分析任务需求；
                            2、选择最合适的节点；
                            3、分配任务；

                            选择节点时考虑: 负载、CPU核数、内存、GPU核数

                            使用service_discovery工具时，必须提供 action 参数：
                            - 查看所有节点: {'action': "discover_services", 'service_type': 'compute'}
                            - 获取网络统计: {'action': 'get_stats'}
                            """
            )

# 4、添加ANP工具
anp_tool = ANPTool(
                name = "service_discovery",
                description = "服务发现工具，可以查找和选择计算节点",
                discovery = discovery
                )

scheduler.add_tool(anp_tool)

# 5、智能分配任务
def assign_task(task_description):
    print (f"任务: {task_description} \n")
    print ('==' * 50)

    # 让Agent智能选择节点
    response = scheduler.run(f"""
                        请为以下任务选择最合适的节点:
                        {task_description}
                        
                        步骤:
                           1、使用 service_discovery 发现工具查看所有可用的计算节点(service_type = 'compute');
                           2、分析每个节点的特点(负载、CPU核数、内存、GPU等);
                           3、根据任务需求选择最合适的节点；
                           4、说明选择理由；

                        请直接给出最终选择节点ID和理由。
                        """)

    print (response)
    print ('**' * 50)

# 测试不同类型的任务
assign_task("训练一个大型的深度学习模型，需要GPU支持")
assign_task("处理大量文本数据，需要高内存")
assign_task("运行轻量级的数据分析")
