"""Authentication utilities: JWT tokens and password hashing."""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

logger = logging.getLogger(__name__)

# JWT configuration
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def create_access_token(user_id: int, role: str) -> str:
    """Create a short-lived access token (15 minutes)."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    """Create a long-lived refresh token (7 days)."""
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict | None:
    """Decode and validate a JWT token. Returns None if invalid."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def hash_token(token: str) -> str:
    """Hash a token for storage in the database (never store raw tokens)."""
    return hashlib.sha256(token.encode()).hexdigest()


def create_reset_token() -> str:
    """Create a random token for password reset."""
    import secrets
    return secrets.token_urlsafe(32)


def send_password_reset_email(
    to_email: str, full_name: str, reset_link: str
) -> None:
    """Send a password reset email via SMTP."""
    import aiosmtplib
    from email.message import EmailMessage

    from app.core.config import settings

    if not settings.SMTP_HOST:
        logger.warning(
            "SMTP not configured. Password reset link for %s: %s",
            to_email,
            reset_link,
        )
        return

    msg = EmailMessage()
    msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    msg["To"] = to_email
    msg["Subject"] = "Recuperação de senha — Casa Afeto"
    msg.set_content(
        f"Olá {full_name},\n\n"
        f"Clique no link abaixo para redefinir sua senha:\n\n"
        f"{reset_link}\n\n"
        f"O link expira em 1 hora.\n"
        f"Se você não pediu para recuperar a senha, ignore este e-mail."
    )

    aiosmtplib.send(
        msg,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        start_tls=True,
        timeout=10,
    )
