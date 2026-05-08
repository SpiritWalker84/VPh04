"""Проверка учётных данных администратора (без отдельных криптобиблиотек)."""

from __future__ import annotations

import hashlib
import hmac


def verify_password(given: str, expected: str) -> bool:
    """Сравнение паролей устойчивым к таймингу образом через хэш фиксированной длины."""
    g = hashlib.sha256(given.encode("utf-8")).digest()
    e = hashlib.sha256(expected.encode("utf-8")).digest()
    return hmac.compare_digest(g, e)
