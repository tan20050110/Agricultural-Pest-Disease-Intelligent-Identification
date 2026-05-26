import hashlib
import secrets

from app.models.database import SessionLocal, User


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
    db = SessionLocal()
    try:
        existing = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing:
            return {"success": False, "message": "用户名或邮箱已存在"}

        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return {"success": True, "message": "注册成功", "user_id": str(user.id)}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"注册失败: {str(e)}"}
    finally:
        db.close()


def login_user(username: str, password: str) -> dict:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return {"success": False, "message": "用户名或密码错误"}
        if not verify_password(password, user.password_hash):
            return {"success": False, "message": "用户名或密码错误"}

        token = generate_token()
        return {
            "success": True,
            "message": "登录成功",
            "token": token,
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "nickname": user.nickname,
                "role": user.role,
                "avatar_url": user.avatar_url,
            }
        }
    except Exception as e:
        return {"success": False, "message": f"登录失败: {str(e)}"}
    finally:
        db.close()