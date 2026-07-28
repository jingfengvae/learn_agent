import sys
import inspect
import gradio as gr

print("Python:", sys.executable)
print("Gradio:", gr.__version__)
print("Gradio file:", gr.__file__)
print("Chatbot signature:")
print(inspect.signature(gr.Chatbot))
