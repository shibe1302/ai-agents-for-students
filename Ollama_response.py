import ollama
import requests
import json
import re
import asyncio
from ollama import AsyncClient

messages = []
MODEL = "llama3.2:3b"

system_promt = {
    "role": "system",
    "content": (
        "You are chatbot about C++ !"
        "1. short answer"
        "2. no need to write many cases"
        "3. no rambling"
        "4. Just a little explanation of the function and variables after generating the code"
        "5. Do not answer if the question lacks context. If context is lacking, ask the user to provide it."
    )
}
messages.append(system_promt)

gl=2
# chia code và text
def separate_code_and_text(text):
    pattern = r'```(?:[\w]+)\n([\s\S]*?)```'
    matches = list(re.finditer(pattern, text, re.DOTALL))
    result = []

    if not matches:
        result.append({'type': 'text', 'content': (0, len(text))})
        return result

    last_index = 0
    for match in matches:
        start, end = match.span()

        if last_index < start:
            result.append({'type': 'text', 'content': (last_index, start - 1)})
        result.append({'type': 'code', 'content': match.span()})
        last_index = end + 1

    if last_index < len(text):
        result.append({'type': 'text', 'content': (last_index, len(text))})

    return result

def chuyen_tublpe_sang_dict(data_input:tuple)->dict:
    for items in data_input:
        messages.append({
            'role': items[0],
            'content': items[2],
        })

def load_old_message(old_mess):
    messages.clear()
    chuyen_tublpe_sang_dict(old_mess)

def new_chat():
    messages.clear()

async def send_receive_response(user_promt):
    client = AsyncClient()
    messages.append(
        {
            'role': 'user',
            'content': user_promt,
        }
    )
    response = await client.chat(model=MODEL,
                                 messages=messages,
                                 stream=False,
                                 )
    assistant_reply = response['message']['content']
    res_da_xu_li=separate_code_and_text(assistant_reply)
    print(assistant_reply)
    messages.append(
        {
            'role': 'assistant',
            'content': assistant_reply,
        }
    )

    return res_da_xu_li,assistant_reply



