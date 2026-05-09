"""Simple Redis response cache for read-heavy endpoints."""
import json
import logging
from typing import Any, Callable

import redis as redis_lib

from app.config import settings

logger = logging.getLogger(__name__)

_CACHE_TTL = 300  # 5 minutes


def _redis() -> redis_lib.Redis:
    return redis_lib.from_url(settings.REDIS_URL, decode_responses=True)


def cache_get(key: str) -> Any | None:
    try:
        raw = _redis().get(key)
        return json.loads(raw) if raw else None
    except Exception as exc:
        logger.warning(f"Cache read failed for {key}: {exc}")
        return None


def cache_set(key: str, value: Any, ttl: int = _CACHE_TTL) -> None:
    try:
        _redis().setex(key, ttl, json.dumps(value, default=str))
    except Exception as exc:
        logger.warning(f"Cache write failed for {key}: {exc}")


def cache_delete(key: str) -> None:
    try:
        _redis().delete(key)
    except Exception as exc:
        logger.warning(f"Cache delete failed for {key}: {exc}")


def cache_delete_pattern(pattern: str) -> None:
    try:
        r = _redis()
        keys = r.keys(pattern)
        if keys:
            r.delete(*keys)
    except Exception as exc:
        logger.warning(f"Cache delete pattern {pattern} failed: {exc}")


def playbook_cache_key(org_id: str) -> str:
    return f"cache:playbook:current:{org_id}"


def textbook_cache_key(org_id: str) -> str:
    return f"cache:textbook:{org_id}"


def checklist_cache_key(org_id: str) -> str:
    return f"cache:checklist:{org_id}"
