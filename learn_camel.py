import os

from camel.models import ModelFactory

from camel.types import ModelPlatformType

from colorama import Fore

from camel.societies import RolePlaying

from camel.utils import print_text_animated

# 定义协作任务
task_prompt = """
            创作一本关于“拖延症心理学”的短篇电子书，目标读者是对心理学感兴趣的普通大众。
            要求：
               1、内容科学严谨，基于实证研究；
               2、语言通俗易懂，避免过多专业术语；
               3、包含实用的改善建议和案例分析；
               4、篇幅控制在8000-10000字；
               5、结构清晰，包含引言、核心章节和总结。
              """
print (Fore.YELLOW + f"协作任务：\n{task_prompt}")

# 初始化角色扮演回话
# AI作家作为"user"，负责提供结构和要求
# AI心里学家作为"assistant",负责提供专业知识和内容

model = ModelFactory.create(
	model_platform=ModelPlatformType.OPENAI,
	model_type = "gpt-4o-mini",
    api_key = "sk-cGxiB1iFm5gm3maLT1LHeFA2XguPZiU2GQ9rMs3wt8pbftcK",
    url = "https://api.chatanywhere.tech"
	)

role_play_session = RolePlaying(
                    assistant_role_name = "心理学家",
                    user_role_name = "作家",
                    task_prompt = task_prompt,
                    model=model,
                    with_task_specify=False)
print (Fore.CYAN + f"具体任务描述：\n {role_play_session.task_prompt}")

chat_turn_limit, n = 30, 0

input_msg = role_play_session.init_chat()

while n < chat_turn_limit:
    n += 1
    assistant_response, user_response = role_play_session.step(input_msg)

    # 检测是否有消息传回
    if assistant_response is None or user_response is None:
        break

    print_text_animated(Fore.BLUE + f"作家: (AI User): \n\n {user_response.msg.content}\n")
    print_text_animated(Fore.GREEN + f"心理专家: (AI Assistant): \n\n {assistant_response.msg.content}\n")
    
    if "<CAMEL_TASK_DONE>" in user_response.msg.content or "<CAMEL_TASK_DONE>" in assistant_response.msg.content:
        print (Fore.MAGENTA + " 电子书创作完成！！\n")
        break
    
    # 将助理的响应作为下一轮的输出
    input_msg = assistant_response.msg

print (Fore.YELLOW + f"总共进行了 {n} 轮协作对话！")