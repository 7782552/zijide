Python

import g4f
from g4f.Provider import Koala

response = g4f.ChatCompletion.create(
    model="gpt-4",
    provider=Koala,
    messages=[{"role": "user", "content": "你好"}],
    stream=False
)
