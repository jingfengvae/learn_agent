from dotenv import load_dotenv

from my_llm import MyLLM

load_dotenv()

llm = MyLLM(provider = "modelscope")

messages = [{"role": "user", "content": "介绍一下你自己"}]

response = llm.think(messages)

print ("ModelScope Response: ")

for chunk in response:
	print (chunk, end="", flush=True)