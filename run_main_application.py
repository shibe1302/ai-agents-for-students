import streamlit as st
from dataBase.chat_history_DB import (
    init_db, save_message, get_messages, get_all_sessions, delete_session, migrate_add_session_name
)
import Ollama_response as OLM
from exercise_handler import (
    get_all_exercises, get_exercise_details, save_submission,
    check_submission, get_user_progress, create_tables_if_not_exist
)
import uuid
import asyncio
import time
import os
import tempfile
import sqlite3

# Initialize databases
init_db()
migrate_add_session_name()
create_tables_if_not_exist()

st.set_page_config(layout="wide", page_title="C++ Learning Platform")
# State management
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_name" not in st.session_state:
    st.session_state.session_name = f"Chat {st.session_state.session_id[:7]}"
if "current_tab" not in st.session_state:
    st.session_state.current_tab = "Chat"
if "current_exercise_id" not in st.session_state:
    st.session_state.current_exercise_id = None
if "total_completed" not in st.session_state:
    st.session_state.total_completed = 0
if "submitted_exercises" not in st.session_state:
    st.session_state.submitted_exercises = {}
if "loaded_completed_exercises" not in st.session_state:
    st.session_state.loaded_completed_exercises = False


def xu_li_chuoi(a):
    if len(a) < 26:
        return a
    else:
        return a[0:25] + "   ..."


def streamtext(text):
    for word in text.split():
        yield word + " "
        time.sleep(0.02)


async def get_code_review(code, exercise_title, results):
    """Get code review from Ollama"""
    passed_tests = results['passed_tests']
    total_tests = results['total_tests']

    prompt = f"""
    Please review this C++ solution and response with VIETNAMESE for the exercise "{exercise_title}".

    Test results: {passed_tests}/{total_tests} tests passed.

    Code:
    ```cpp
    {code}
    ```

    Provide a brief review:
    - If all tests passed: praise good aspects of the code and suggest any optimizations
    - If some tests failed: identify possible issues and suggest improvements
    - Comment on code style, efficiency, and best practices

    Keep your review concise and constructive.
    """

    txt_index, txt_plain = await OLM.send_receive_response(prompt)
    return txt_index, txt_plain


# Main application layout with tabs
tab1, tab2 = st.tabs(["Chat", "Exercises"])

# TAB 1: CHAT
with tab1:
    st.title("Chatbot thiểu năng 🤖")

    # Load messages
    if not st.session_state.messages:
        st.session_state.messages = get_messages(st.session_state.session_id)

    # Display messages
    for msg in st.session_state.messages:
        with st.chat_message(msg[0]):
            if msg[1] == "code":
                st.code(msg[2])
            else:
                st.markdown(msg[2])

    # Chat input
if prompt := st.chat_input("Nhập tin nhắn..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append(("user", "text", prompt))
    save_message(st.session_state.session_id, "user", prompt, "text", st.session_state.session_name)

    # Bot response
    with st.chat_message("assistant"):
        with st.spinner("Chờ tí...", show_time=True):
            txt_index, txt_plain = asyncio.run(OLM.send_receive_response(prompt))
        with st.container():
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
                    st.session_state.messages.append(("assistant", "code", code_piece))
    save_message(st.session_state.session_id, "assistant", txt_plain, "text", st.session_state.session_name)
    st.rerun()

# TAB 2: EXERCISES
with tab2:
    st.title("C++ Exercises")

    # Get user progress
    total_exercises = len(get_all_exercises())
    completed_exercises = get_user_progress()
    progress_percentage = completed_exercises / total_exercises if total_exercises > 0 else 0

    # Load completed exercises once when the tab is first opened
    if not st.session_state.loaded_completed_exercises:
        conn = sqlite3.connect("dataBase/exercises.db")
        cursor = conn.cursor()
        cursor.execute("SELECT exercise_id FROM user_progress WHERE completed = 1")
        completed_exercises_ids = [row[0] for row in cursor.fetchall()]
        conn.close()

        # Mark these exercises as completed in the session state
        for ex_id in completed_exercises_ids:
            st.session_state.submitted_exercises[ex_id] = {'passed_all': True}

        st.session_state.loaded_completed_exercises = True
    # Progress bar
    st.progress(progress_percentage)
    st.write(f"Completed: {completed_exercises}/{total_exercises}")

    # Exercise list
    exercises = get_all_exercises()
    for ex in exercises:
        ex_id, title, difficulty = ex

        # Check if exercise is completed and add visual indicator
        is_completed = ex_id in st.session_state.submitted_exercises and st.session_state.submitted_exercises[ex_id][
            'passed_all']

        # Show completion status in the expander title
        expander_title = f"Ex{ex_id}: {title} ({difficulty}) {'✅' if is_completed else ''}"

        with st.expander(expander_title):
            exercise_data = get_exercise_details(ex_id)

            if exercise_data:
                st.markdown(exercise_data['description'])

                # File uploader
                uploaded_file = st.file_uploader("Upload your C++ solution",
                                                 type=['cpp'],
                                                 key=f"upload_{ex_id}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Submit Solution", key=f"submit_{ex_id}"):
                        if uploaded_file:
                            # Save the uploaded file to a temporary location
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.cpp') as tmp_file:
                                tmp_file.write(uploaded_file.getvalue())
                                tmp_path = tmp_file.name

                            # Check the submission against test cases
                            results = check_submission(ex_id, tmp_path)
                            code_content = uploaded_file.getvalue().decode('utf-8')

                            # Store the submission
                            submission_id = save_submission(ex_id, code_content, results)

                            # Display results
                            # After checking submission and displaying results
                            st.subheader("Results")
                            # Use columns with appropriate ratios or full width
                            full_col = st.columns([1])[0]  # Using a single column that takes full width
                            with full_col:
                                # Just use the full width of the container without creating columns
                                st.write(f"Passed test cases: {results['passed_tests']}/{results['total_tests']}")

                                if results['passed_tests'] == results['total_tests']:
                                    st.success("All tests passed! Great work!")
                                    # Don't increment if already completed
                                    if ex_id not in st.session_state.submitted_exercises or not \
                                            st.session_state.submitted_exercises[ex_id]['passed_all']:
                                        st.session_state.total_completed += 1
                                        st.session_state.submitted_exercises[ex_id] = {'passed_all': True}
                                else:
                                    st.error("Some tests failed. Check the details below.")
                                    st.session_state.submitted_exercises[ex_id] = {'passed_all': False}

                                # Display feedback
                                st.subheader("Feedback")
                                st.code(results['feedback'], language="text")

                                # Get and display code review from Ollama
                                st.subheader("Code Review")
                                with st.spinner("Getting code review..."):
                                    review_index, review_plain = asyncio.run(
                                        get_code_review(code_content, title, results))

                                    # Display the review
                                    for item in review_index:
                                        start, end = item['content']
                                        if item['type'] == 'text':
                                            text_piece = review_plain[start:end]
                                            st.markdown(text_piece)
                                        elif item['type'] == 'code':
                                            code_piece = review_plain[start:end]
                                            st.code(code_piece, language="cpp")

                            # Clean up
                            os.unlink(tmp_path)
                        else:
                            st.error("Please upload your C++ solution first.")

# Sidebar
st.sidebar.title("Lịch sử chat")

if st.sidebar.button("ㅤ➕ New Chatㅤ"):
    # Reset session state
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.session_name = f"Chat {st.session_state.session_id[:7]}"
    st.session_state.messages = []
    # Clear Ollama context before rerun
    OLM.new_chat()
    # Force a complete rerun by clearing the cache
    st.cache_data.clear()
    st.rerun()

# Chat history list
st.sidebar.markdown("### 🗂️ Danh sách hội thoại:")
# Add this near the top of your sidebar
st.sidebar.caption(f"Current session: {st.session_state.session_name}")
sessions = get_all_sessions()
for sess_id, sess_name in sessions:
    col1, col2 = st.sidebar.columns([4, 1])
    current_mess = get_messages(sess_id)[0][2] if get_messages(sess_id) else "Empty chat"
    name_of_chat = xu_li_chuoi(current_mess)

    with col1:
        if st.button(name_of_chat, key=f"load_{sess_id}"):
            # Set new session state
            st.session_state.session_id = sess_id
            st.session_state.messages = get_messages(sess_id)
            st.session_state.session_name = sess_name
            # Update Ollama context
            OLM.load_old_message(st.session_state.messages)
            # Force a complete rerun with cache clearing
            st.cache_data.clear()
            st.rerun()

    with col2:
        if st.button("❌", key=f"delete_{sess_id}"):
            delete_session(sess_id)
            if st.session_state.session_id == sess_id:
                st.session_state.session_id = str(uuid.uuid4())
                st.session_state.session_name = f"Chat {st.session_state.session_id[:4]}"
                st.session_state.messages = []
            st.rerun()