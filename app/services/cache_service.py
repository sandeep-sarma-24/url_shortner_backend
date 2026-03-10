"""
Two-tier URL cache: L1 in-process LRU (bounded memory, zero-latency)
backed by L2 Redis (shared across workers, survives restarts).

Lookup: L1 -> L2 -> DB.  On DB hit the value is promoted into both layers.
Invalidation removes from both layers so stale data is never served.
"""

from __future__ import annotations

import logging
import threading
from collections import OrderedDict
from typing import Optional

import redis as sync_redis

from app.configs.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

REDIS_KEY_PREFIX = "shortr:url:"
CACHE_TTL = settings.CACHE_TTL_SECONDS
LRU_MAX_SIZE = settings.CACHE_LRU_MAX_SIZE


class LRUCache:
    """Thread-safe, bounded LRU cache for the hot-path redirect lookup."""

    def __init__(self, max_size: int = LRU_MAX_SIZE):
        self._store: OrderedDict[str, str] = OrderedDict()
        self._max_size = max_size
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[str]:
        with self._lock:
            if key not in self._store:
                return None
            self._store.move_to_end(key)
            return self._store[key]

    def put(self, key: str, value: str) -> None:
        with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
                self._store[key] = value
            else:
                if len(self._store) >= self._max_size:
                    self._store.popitem(last=False)
                self._store[key] = value

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


_lru = LRUCache()

_redis: Optional[sync_redis.Redis] = None


def init_redis() -> None:
    """Connect to Redis. Call once at app startup."""
    global _redis
    try:
        _redis = sync_redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
            retry_on_timeout=True,
        )
        _redis.ping()
        logger.info("Redis connected at %s", settings.REDIS_URL)
    except Exception:
        logger.warning("Redis unavailable – falling back to LRU-only caching")
        _redis = None


def close_redis() -> None:
    global _redis
    if _redis is not None:
        try:
            _redis.close()
        except Exception:
            pass
        _redis = None
    _lru.clear()


def _redis_key(short_code: str) -> str:
    return f"{REDIS_KEY_PREFIX}{short_code}"


def get_cached_url(short_code: str) -> Optional[str]:
    """L1 (LRU) -> L2 (Redis) lookup.  Returns original URL or None."""
    url = _lru.get(short_code)
    if url is not None:
        logger.info("Cache HIT (L1 LRU) for %s", short_code)
        return url

    if _redis is not None:
        try:
            url = _redis.get(_redis_key(short_code))
            if url is not None:
                logger.info("Cache HIT (L2 Redis) for %s", short_code)
                _lru.put(short_code, url)
                return url
        except Exception:
            logger.debug("Redis read failed for %s", short_code, exc_info=True)

    logger.info("Cache MISS for %s", short_code)
    return None


def set_cached_url(short_code: str, original_url: str) -> None:
    """Promote a DB result into both cache layers."""
    _lru.put(short_code, original_url)

    if _redis is not None:
        try:
            _redis.setex(_redis_key(short_code), CACHE_TTL, original_url)
        except Exception:
            logger.debug("Redis write failed for %s", short_code, exc_info=True)


def invalidate_cache(short_code: str) -> None:
    """Remove from both layers – used on URL update / delete."""
    _lru.delete(short_code)

    if _redis is not None:
        try:
            _redis.delete(_redis_key(short_code))
        except Exception:
            logger.debug("Redis delete failed for %s", short_code, exc_info=True)
