import torch
import numpy
from transformers import AutoModelForCausalLM, AutoTokenizer

model_id = 'QWen/QWen1.5-0.5B-Chat'

device = 'cuda' if torch.cuda.is_available() else "cpu"

print (f"using device: {device}")

# 加载分词器
tokenizer = AutoTokenizer.from_pretrained(model_id)

# 加载模型
model = AutoModelForCausalLM.from_pretrained(model_id).to(device)

print ("模型和分词器加载完成")