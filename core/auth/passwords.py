"""Утилиты для хранения и проверки паролей.

Формат password_hash:
    pbkdf2_sha256$<iterations>$<salt_b64>$<hash_b64>
"""

from __future__ import annotations

import base64
import hmac
import os
from dataclasses import dataclass
from hashlib import pbkdf2_hmac, sha256


@dataclass(frozen=True, slots=True)
class PasswordHashParams:
    iterations: int = 210_000
    salt_bytes: int = 16


def hash_password(password: str, *, params: PasswordHashParams = PasswordHashParams()) -> str:
    if password == "":
        raise ValueError("password не должен быть пустым.")
    if params.iterations <= 0:
        raise ValueError("params.iterations должен быть > 0.")
    if params.salt_bytes <= 0:
        raise ValueError("params.salt_bytes должен быть > 0.")

    salt = os.urandom(params.salt_bytes)
    dk = pbkdf2_hmac("sha256", password.encode("utf-8"), salt, params.iterations)
    salt_b64 = base64.urlsafe_b64encode(salt).decode("ascii").rstrip("=")
    dk_b64 = base64.urlsafe_b64encode(dk).decode("ascii").rstrip("=")
    return f"pbkdf2_sha256${params.iterations}${salt_b64}${dk_b64}"


def verify_password(password: str, password_hash: str) -> bool:
    if password == "":
        raise ValueError("password не должен быть пустым.")
    if password_hash == "":
        raise ValueError("password_hash не должен быть пустым.")

    parts = password_hash.split("$")
    if len(parts) != 4:
        raise ValueError("Некорректный формат password_hash.")
    scheme, iterations_raw, salt_b64, dk_b64 = parts
    if scheme != "pbkdf2_sha256":
        raise ValueError("Неподдерживаемая схема password_hash.")

    try:
        iterations = int(iterations_raw)
    except ValueError as exc:
        raise ValueError("Некорректное iterations в password_hash.") from exc
    if iterations <= 0:
        raise ValueError("iterations в password_hash должен быть > 0.")

    salt = _b64url_decode(salt_b64)
    expected = _b64url_decode(dk_b64)
    actual = pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(expected, actual)


def _b64url_decode(data: str) -> bytes:
    padded = data + "=" * ((4 - (len(data) % 4)) % 4)
    try:
        return base64.urlsafe_b64decode(padded.encode("ascii"))
    except Exception as exc:
        raise ValueError("Некорректный base64 в password_hash.") from exc

