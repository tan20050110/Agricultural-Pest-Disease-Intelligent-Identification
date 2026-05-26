import hashlib
import secrets
import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).parent.parent.parent / "data" / "users.db"
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nickname TEXT,
            role TEXT DEFAULT 'user',
            avatar_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.sha256((password + salt).encode("utf-8")).hexdigest()
    return f"{salt}${h}"


def verify_password(password: str, password_hash: str) -> bool:
    parts = password_hash.split("$", 1)
    if len(parts) != 2:
        return False
    salt, stored_hash = parts
    h = hashlib.sha256((password + salt).encode("utf-8")).hexdigest()
    return h == stored_hash


def generate_token() -> str:
    return secrets.token_hex(32)


def register_user(username: str, email: str, password: str) -> dict:
    init_database()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
        existing = cursor.fetchone()
        if existing:
            return {"success": False, "message": "用户名或邮箱已存在"}

        password_hash = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash)
        )
        conn.commit()
        user_id = cursor.lastrowid
        return {"success": True, "message": "注册成功", "user_id": str(user_id)}
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": f"注册失败: {str(e)}"}
    finally:
        conn.close()


def login_user(username: str, password: str) -> dict:
    init_database()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        if not user:
            return {"success": False, "message": "用户名或密码错误"}
        if not verify_password(password, user["password_hash"]):
            return {"success": False, "message": "用户名或密码错误"}

        token = generate_token()
        return {
            "success": True,
            "message": "登录成功",
            "token": token,
            "user": {
                "id": str(user["id"]),
                "username": user["username"],
                "email": user["email"],
                "nickname": user["nickname"] or user["username"],
                "role": user["role"],
                "avatar_url": user["avatar_url"],
            }
        }
    except Exception as e:
        return {"success": False, "message": f"登录失败: {str(e)}"}
    finally:
        conn.close()
