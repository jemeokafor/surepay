from aiocache import Cache, cached
from aiocache.serializers import PickleSerializer
import asyncio
import logging
from typing import Any, Optional
import hashlib

logger = logging.getLogger(__name__)

class SurePayCache:
    """
    Caching module for SurePay application
    """
    
    def __init__(self, cache_type: str = "memory", **kwargs):
        """
        Initialize cache with specified type
        """
        if cache_type == "memory":
            self.cache = Cache(Cache.MEMORY, serializer=PickleSerializer(), **kwargs)
        elif cache_type == "redis":
            # For production, you would configure Redis connection
            self.cache = Cache(
                Cache.REDIS, 
                endpoint=kwargs.get("endpoint", "localhost"),
                port=kwargs.get("port", 6379),
                serializer=PickleSerializer(),
                **kwargs
            )
        else:
            # Default to memory cache
            self.cache = Cache(Cache.MEMORY, serializer=PickleSerializer(), **kwargs)
    
    async def get(self, key: str) -> Any:
        """
        Get value from cache
        """
        try:
            return await self.cache.get(key)
        except Exception as e:
            logger.warning(f"Cache get error: {str(e)}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """
        Set value in cache with TTL (time to live)
        """
        try:
            await self.cache.set(key, value, ttl=ttl)
            return True
        except Exception as e:
            logger.warning(f"Cache set error: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete value from cache
        """
        try:
            await self.cache.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete error: {str(e)}")
            return False
    
    async def clear(self) -> bool:
        """
        Clear all cache entries
        """
        try:
            await self.cache.clear()
            return True
        except Exception as e:
            logger.warning(f"Cache clear error: {str(e)}")
            return False
    
    def generate_key(self, prefix: str, *args) -> str:
        """
        Generate cache key from prefix and arguments
        """
        key_string = f"{prefix}:" + ":".join(str(arg) for arg in args)
        return hashlib.md5(key_string.encode()).hexdigest()

# Global cache instances
memory_cache = SurePayCache("memory")
redis_cache = None  # Initialize in production with Redis config

def get_cache(cache_type: str = "memory") -> SurePayCache:
    """
    Get cache instance
    """
    if cache_type == "redis" and redis_cache:
        return redis_cache
    return memory_cache

def cache_key(prefix: str, *args) -> str:
    """
    Generate cache key
    """
    return memory_cache.generate_key(prefix, *args)

# Cache decorators for common operations
def cached_transaction(ttl: int = 300):
    """
    Cache decorator for transaction operations
    """
    def wrapper(func):
        return cached(
            ttl=ttl,
            key_builder=lambda f, *args, **kwargs: cache_key("transaction", *args),
            cache=Cache.MEMORY
        )(func)
    return wrapper

def cached_vendor(ttl: int = 600):
    """
    Cache decorator for vendor operations
    """
    def wrapper(func):
        return cached(
            ttl=ttl,
            key_builder=lambda f, *args, **kwargs: cache_key("vendor", *args),
            cache=Cache.MEMORY
        )(func)
    return wrapper

def cached_payout(ttl: int = 300):
    """
    Cache decorator for payout operations
    """
    def wrapper(func):
        return cached(
            ttl=ttl,
            key_builder=lambda f, *args, **kwargs: cache_key("payout", *args),
            cache=Cache.MEMORY
        )(func)
    return wrapper

# Cache warming functions
async def warm_transaction_cache(transaction_id: str, transaction_data: dict):
    """
    Preload transaction data into cache
    """
    cache = get_cache()
    key = cache_key("transaction", transaction_id)
    await cache.set(key, transaction_data, ttl=300)

async def warm_vendor_cache(vendor_id: str, vendor_data: dict):
    """
    Preload vendor data into cache
    """
    cache = get_cache()
    key = cache_key("vendor", vendor_id)
    await cache.set(key, vendor_data, ttl=600)

async def warm_payout_cache(transaction_id: str, payout_data: dict):
    """
    Preload payout data into cache
    """
    cache = get_cache()
    key = cache_key("payout", transaction_id)
    await cache.set(key, payout_data, ttl=300)