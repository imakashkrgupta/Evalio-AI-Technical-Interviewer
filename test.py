import ollama
from ollama import chat
from ollama import ChatResponse

response = ollama.generate(model='llama3.2:1b', prompt='Why is the sky blue?')

print(response.message.content)