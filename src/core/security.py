import hashlib
import secrets

import bcrypt


def hash_password(raw_password: str) -> str:
    """Хешируем пароль в открытом виде с использованием алгоритма bcrypt."""
    return bcrypt.hashpw(raw_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(raw_password: str, hashed_password: str) -> bool:
    """Проверяем соответствие сырого пароля его сохраненному криптографическому хешу."""
    return bcrypt.checkpw(raw_password.encode("utf-8"), hashed_password.encode("utf-8"))


def generate_session_token() -> str:
    """Случайный opaque-токен, отдаётся клиенту один раз в чистом виде."""
    return secrets.token_urlsafe(32)


def hash_token(raw_token: str) -> str:
    """
    Токен в БД хранится только в виде хэша (аналогично паролю), чтобы при утечке
    базы нельзя было использовать значения напрямую как Bearer-токены.
    """
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
