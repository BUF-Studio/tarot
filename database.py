import sqlite3

def init_db():
    conn = sqlite3.connect('tarot_reading.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            sender_id TEXT PRIMARY KEY,
            question TEXT,
            cards TEXT,
            summary TEXT,
            current_card INTEGER,
            stage TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_session(sender_id):
    conn = sqlite3.connect('tarot_reading.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM sessions WHERE sender_id = ?', (sender_id,))
    session = cursor.fetchone()
    conn.close()
    return session

def create_or_update_session(sender_id, question, cards, summary, current_card, stage):
    conn = sqlite3.connect('tarot_reading.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sessions (sender_id, question, cards, summary, current_card, stage)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(sender_id) DO UPDATE SET
            question = excluded.question,
            cards = excluded.cards,
            summary = excluded.summary,
            current_card = excluded.current_card,
            stage = excluded.stage
    ''', (sender_id, question, cards, summary, current_card, stage))
    conn.commit()
    conn.close()

def clear_session(sender_id):
    conn = sqlite3.connect('tarot_reading.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM sessions WHERE sender_id = ?', (sender_id,))
    conn.commit()
    conn.close()
