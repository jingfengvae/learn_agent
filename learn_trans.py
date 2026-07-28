import torch
import numpy
from transformers import AutoModelForCausalLM, AutoTokenizer

model_id = 'Qwen/Qwen1.5-0.5B-Chat'

device = 'cuda' if torch.cuda.is_available() else "cpu"

print (f"using device: {device}")

# 加载分词器
tokenizer = AutoTokenizer.from_pretrained(model_id)

# 加载模型
model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True, device_map="auto")

print ("模型和分词器加载完成")

message = [{"role": "system", "content": "You are a helpful assistant."},
           {"role": "user", "content": "你好， 请你介绍下你自己！"}]

# 使用分词器的模版格式化输入

text = tokenizer.apply_chat_template(message, tokenize=False, add_generation_prompt=True)

model_inputs = tokenizer([text], return_tensors="pt").to(device)

print ("编码后的输入文本：")
print (model_inputs)


generated_ids = model.generate(model_inputs.input_ids, max_new_tokens=512)

generated_ids = [output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)]

response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

print (response)