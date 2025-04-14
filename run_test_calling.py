import asyncio

from Ollama_response import send_receive_response

while True:
    chat = input(">>> ")
    if chat == "/exit":
        break
    elif len(chat) > 0:
        asyncio.run(send_receive_response(chat))
