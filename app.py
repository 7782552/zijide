import g4f
from g4f.Provider import Chatgpt4Online

response = g4f.ChatCompletion.create(
    model="gpt-4",
    provider=Chatgpt4Online,
    messages=[{"role": "user", "content": "你好"}],
    stream=False
)
print(response)
