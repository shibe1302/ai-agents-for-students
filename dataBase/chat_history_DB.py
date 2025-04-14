import sqlite3
from datetime import datetime

DB_NAME = "chat_history_DB.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            session_name TEXT,   -- thêm dòng này!
            role TEXT,
            type TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def migrate_add_session_name():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE chats ADD COLUMN session_name TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Cột đã tồn tại, bỏ qua lỗi
    conn.close()


def save_message(session_id, role, message,type1, session_name=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO chats (session_id, session_name, role, message,type) VALUES (?, ?, ?, ?,?)',
              (session_id, session_name, role, message,type1))
    conn.commit()
    conn.close()

def save_session_name(session_id, session_name):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('UPDATE chats SET session_name = ? WHERE session_id = ?', (session_name, session_id))
    conn.commit()
    conn.close()

def get_messages(session_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT role,type, message FROM chats WHERE session_id = ? ORDER BY timestamp ASC', (session_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def delete_session(session_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM chats WHERE session_id = ?', (session_id,))
    conn.commit()
    conn.close()

def get_all_sessions():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        SELECT session_id, COALESCE(session_name, session_id) 
        FROM chats 
        GROUP BY session_id 
        ORDER BY MAX(timestamp) DESC
    ''')
    sessions = c.fetchall()
    conn.close()
    return sessions  # [(id, name)]