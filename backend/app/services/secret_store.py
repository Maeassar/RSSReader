from __future__ import annotations

import base64
import hashlib
import hmac
import os
import platform
import secrets
from pathlib import Path


PREFIX = "enc:v1:"
_MAC_SIZE = 16
_NONCE_SIZE = 16


def encrypt_secret(value: str | None) -> str:
    plaintext = (value or "").encode("utf-8")
    if not plaintext:
        return ""
    if is_encrypted_secret(value or ""):
        return value or ""
    nonce = secrets.token_bytes(_NONCE_SIZE)
    ciphertext = _xor_bytes(plaintext, _keystream(nonce, len(plaintext)))
    mac = hmac.new(_key(), b"v1" + nonce + ciphertext, hashlib.sha256).digest()[:_MAC_SIZE]
    payload = base64.urlsafe_b64encode(nonce + mac + ciphertext).decode("ascii")
    return PREFIX + payload


def decrypt_secret(value: str | None) -> str:
    token = value or ""
    if not token:
        return ""
    if not is_encrypted_secret(token):
        return token
    try:
        raw = base64.urlsafe_b64decode(token[len(PREFIX):].encode("ascii"))
        nonce = raw[:_NONCE_SIZE]
        mac = raw[_NONCE_SIZE:_NONCE_SIZE + _MAC_SIZE]
        ciphertext = raw[_NONCE_SIZE + _MAC_SIZE:]
        expected = hmac.new(_key(), b"v1" + nonce + ciphertext, hashlib.sha256).digest()[:_MAC_SIZE]
        if not hmac.compare_digest(mac, expected):
            return ""
        plaintext = _xor_bytes(ciphertext, _keystream(nonce, len(ciphertext)))
        return plaintext.decode("utf-8")
    except Exception:
        return ""


def is_encrypted_secret(value: str | None) -> bool:
    return bool(value and value.startswith(PREFIX))


def _key() -> bytes:
    configured = os.environ.get("RSSREADER_SECRET_KEY") or os.environ.get("RSSREADER_KEY_ENCRYPTION_SECRET")
    if configured:
        seed = configured
    else:
        seed = "|".join(
            [
                platform.node(),
                os.environ.get("USER") or os.environ.get("USERNAME") or "",
                str(Path.home()),
            ]
        )
    return hashlib.sha256(seed.encode("utf-8")).digest()


def _keystream(nonce: bytes, length: int) -> bytes:
    blocks: list[bytes] = []
    counter = 0
    while sum(len(block) for block in blocks) < length:
        blocks.append(hmac.new(_key(), nonce + counter.to_bytes(4, "big"), hashlib.sha256).digest())
        counter += 1
    return b"".join(blocks)[:length]


def _xor_bytes(left: bytes, right: bytes) -> bytes:
    return bytes(a ^ b for a, b in zip(left, right))
