"""JWT утилиты проекта sync.

Реализация намеренно минимальная и строгая:
- поддерживается только HMAC (HS256);
- обязательны поля exp и sub;
- никакие значения не угадываются.
"""

from __future__ import annotations

import base64
import hmac
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padded = data + "=" * ((4 - (len(data) % 4)) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


@dataclass(frozen=True, slots=True)
class JwtClaims:
    sub: str
    exp: datetime
    raw: dict[str, Any]


def encode_hs256(claims: dict[str, Any], *, secret: str) -> str:
    if not secret:
        raise ValueError("secret обязателен для подписи JWT.")
    if "exp" not in claims:
        raise ValueError("JWT claims.exp обязателен.")
    if "sub" not in claims:
        raise ValueError("JWT claims.sub обязателен.")

    header = {"typ": "JWT", "alg": "HS256"}
    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(claims, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    signature = hmac.new(secret.encode("utf-8"), signing_input, sha256).digest()
    return f"{header_b64}.{payload_b64}.{_b64url_encode(signature)}"


def decode_and_verify(token: str, *, secret: str, algorithm: str) -> JwtClaims:
    if not token:
        raise ValueError("token обязателен.")
    if not secret:
        raise ValueError("secret обязателен.")
    if algorithm != "HS256":
        raise ValueError(f"Неподдерживаемый jwt_algorithm: {algorithm!r}.")

    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Некорректный JWT: ожидались 3 части.")

    header_raw = _b64url_decode(parts[0])
    payload_raw = _b64url_decode(parts[1])
    signature = _b64url_decode(parts[2])

    try:
        header = json.loads(header_raw.decode("utf-8"))
        payload = json.loads(payload_raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Некорректный JWT: не удалось декодировать JSON.") from exc

    if header.get("typ") != "JWT":
        raise ValueError("Некорректный JWT: header.typ должен быть 'JWT'.")
    if header.get("alg") != algorithm:
        raise ValueError("Некорректный JWT: header.alg не совпадает с ожидаемым.")

    signing_input = f"{parts[0]}.{parts[1]}".encode("ascii")
    expected = hmac.new(secret.encode("utf-8"), signing_input, sha256).digest()
    if not hmac.compare_digest(signature, expected):
        raise ValueError("Некорректный JWT: подпись не совпадает.")

    sub = payload.get("sub")
    if not isinstance(sub, str) or sub == "":
        raise ValueError("Некорректный JWT: payload.sub обязателен и должен быть строкой.")

    exp_value = payload.get("exp")
    if not isinstance(exp_value, (int, float)):
        raise ValueError("Некорректный JWT: payload.exp обязателен и должен быть unix timestamp.")
    exp_dt = datetime.fromtimestamp(float(exp_value), tz=UTC)
    if exp_dt <= datetime.now(tz=UTC):
        raise ValueError("JWT истёк (exp).")

    return JwtClaims(sub=sub, exp=exp_dt, raw=payload)

