"""
Simple in-memory cache for session data with TTL.

Reduces file I/O by caching read_sessions() results for a short period.
"""

import logging
import time
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

# Cache storage: {cache_key: (data, expiry_time)}
_cache: dict[str, tuple[Any, float]] = {}

# Default TTL: 30 seconds
DEFAULT_TTL_SECONDS = 30


def _make_cache_key(date: datetime) -> str:
    """Generate cache key for a date."""
    return f"sessions_{date.strftime('%d-%m-%Y')}"


def get_cached_sessions(date: datetime) -> Optional[list[dict[str, Any]]]:
    """
    Get cached sessions for a date if available and not expired.
    
    Args:
        date: The date to get sessions for.
        
    Returns:
        Cached sessions list if available and fresh, None otherwise.
    """
    key = _make_cache_key(date)
    if key in _cache:
        data, expiry = _cache[key]
        if time.time() < expiry:
            logger.debug("Cache hit for %s", key)
            return data
        else:
            # Expired, remove it
            del _cache[key]
            logger.debug("Cache expired for %s", key)
    return None


def set_cached_sessions(date: datetime, sessions: list[dict[str, Any]], ttl: int = DEFAULT_TTL_SECONDS) -> None:
    """
    Cache sessions for a date with TTL.
    
    Args:
        date: The date to cache sessions for.
        sessions: The sessions data to cache.
        ttl: Time-to-live in seconds (default: 30s).
    """
    key = _make_cache_key(date)
    expiry = time.time() + ttl
    _cache[key] = (sessions, expiry)
    logger.debug("Cached %d sessions for %s (TTL: %ds)", len(sessions), key, ttl)


def invalidate_cache(date: Optional[datetime] = None) -> None:
    """
    Invalidate cache entries.
    
    Args:
        date: If provided, only invalidate this specific date. 
              If None, clear entire cache.
    """
    if date is None:
        _cache.clear()
        logger.info("Cache cleared (all entries)")
    else:
        key = _make_cache_key(date)
        if key in _cache:
            del _cache[key]
            logger.info("Cache invalidated for %s", key)


def cache_sessions(ttl: int = DEFAULT_TTL_SECONDS) -> Callable:
    """
    Decorator to cache read_sessions() results.
    
    Args:
        ttl: Time-to-live in seconds (default: 30s).
        
    Returns:
        Decorated function with caching.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(date: Optional[datetime] = None) -> list[dict[str, Any]]:
            if date is None:
                date = datetime.now()
            
            # Try cache first
            cached = get_cached_sessions(date)
            if cached is not None:
                # Return a copy to prevent cache pollution
                return list(cached)
            
            # Cache miss, call original function
            logger.debug("Cache miss, reading from disk for %s", date.strftime('%d-%m-%Y'))
            result = func(date)
            
            # Cache a copy of the result to prevent external modifications
            set_cached_sessions(date, list(result), ttl=ttl)
            
            return result
        return wrapper
    return decorator


def get_cache_stats() -> dict[str, Any]:
    """
    Get cache statistics.
    
    Returns:
        Dictionary with cache stats.
    """
    now = time.time()
    active_entries = sum(1 for _, expiry in _cache.values() if now < expiry)
    expired_entries = len(_cache) - active_entries
    
    return {
        "total_entries": len(_cache),
        "active_entries": active_entries,
        "expired_entries": expired_entries,
        "cache_keys": list(_cache.keys())
    }
