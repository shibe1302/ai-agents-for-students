# ollama_api.py
import requests
import json
import re


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


def get_response(chat_messages, prompt):
    chat_messages.append({"role": "user", "content": prompt})
    try:
        response = requests.post(url, json={
            "model": "llama3.2:3b",
            "messages": chat_messages
        }, stream=False)

        if response.status_code == 200:
            final = ""
            for line in response.iter_lines():
                if line:
                    result = json.loads(line.decode("utf-8"))
                    content_piece = result.get("message", {}).get("content", "")
                    final += content_piece
            chat_messages.append({"role": "assistant", "content": final})
            return separate_code_and_text(final), final
        else:
            print(f"Lỗi: Server trả về mã trạng thái {response.status_code}")
    except Exception as e:
        print(f"Lỗi kết nối: {e}")
    return [], ""
