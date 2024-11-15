import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_user(username, password, email):
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        password_hash = generate_password_hash(password)
        c.execute('INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)',
                 (username, password_hash, email))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    conn.close()
    
    if result:
        return check_password_hash(result[0], password)
    return False