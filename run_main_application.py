import streamlit as st


from dataBase.chat_history_DB import (
    init_db, save_message, get_messages, get_all_sessions, delete_session,migrate_add_session_name
)
import Ollama_response as OLM
import uuid
import asyncio
import time

init_db()
migrate_add_session_name()



# State
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_name" not in st.session_state:
    st.session_state.session_name = f"Chat {st.session_state.session_id[:7]}"

# Sidebar
st.sidebar.title("Lịch sử chat")


if st.sidebar.button("ㅤ➕ New Chatㅤ"):
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.session_name = f"Chat {st.session_state.session_id[:7]}"
    st.session_state.messages = []
    OLM.new_chat()

def get_first_promt():
    pass
    print(st.session_state.messages)

def xu_li_chuoi(a):
    ten_doan_chat=""
    if(len(a)<26):
        return a
    else:
        return a[0:25]+"   ..."

def streamtext(text):
    for word in text.split():
        yield word + " "
        time.sleep(0.02)

# Hiển thị danh sách phiên
st.sidebar.markdown("### 🗂️ Danh sách hội thoại:")
sessions = get_all_sessions()
for sess_id, sess_name in sessions:
    col1, col2 = st.sidebar.columns([4, 1])
    current_mess=get_messages(sess_id)[0][2]
    name_of_chat=xu_li_chuoi(current_mess)
    with col1:
        if st.button(name_of_chat, key=f"load_{sess_id}"):
            st.session_state.session_id = sess_id
            st.session_state.messages = get_messages(sess_id)
            OLM.load_old_message(st.session_state.messages)
            st.session_state.session_name = sess_name


    with col2:
        if st.button("❌", key=f"delete_{sess_id}"):
            delete_session(sess_id)
            if st.session_state.session_id == sess_id:
                st.session_state.session_id = str(uuid.uuid4())
                st.session_state.session_name = f"Chat {st.session_state.session_id[:4]}"
                st.session_state.messages = []
            st.rerun()

# Main chat
st.title("Chatbot thiểu năng 🤖")

# Load messages
if not st.session_state.messages:
    st.session_state.messages = get_messages(st.session_state.session_id)


# for role, msg in st.session_state.messages:
#     with st.chat_message(role):
#         st.markdown(msg)
for msg in st.session_state.messages:
    # print("mgs ----- ",msg)
    with st.chat_message(msg[0]):
        if msg[1] == "code":
            st.code(msg[2])  # hoặc st.code(...) nếu muốn đẹp hơn
        else:
            st.markdown(msg[2])


if prompt := st.chat_input("Nhập tin nhắn..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append(("user","text",prompt))
    save_message(st.session_state.session_id, "user", prompt,"text", st.session_state.session_name)
    # Giả lập phản hồi bot
    with st.chat_message("assistant"):
        with st.spinner("Chờ tí...", show_time=True):
            txt_index, txt_plain = asyncio.run(OLM.send_receive_response(prompt))
        with st.container():  # gom chung tất cả vào một khối
            for item in txt_index:
                start, end = item['content']
                if item['type'] == 'text':
                    text_piece = txt_plain[start:end]
                    st.write_stream(streamtext(text_piece))
                    st.session_state.messages.append(
                        ("assistant", "text", text_piece)
                    )
                elif item['type'] == 'code':
                    code_piece = txt_plain[start:end]
                    st.code(code_piece, language="cpp")
                    st.session_state.messages.append(("assistant","code",code_piece))
    save_message(st.session_state.session_id, "assistant", txt_plain,"text", st.session_state.session_name)
    st.rerun()
