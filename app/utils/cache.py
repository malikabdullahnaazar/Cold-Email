import json
import asyncio
from typing import Any, Optional, Union
from datetime import datetime, timedelta
import redis.asyncio as redis
from app.config import settings
from app.utils.logger import logger


class CacheManager:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.memory_cache: dict = {}
        self._setup_redis()
    
    def _setup_redis(self):
        """Setup Redis connection if available"""
        if settings.redis_url:
            try:
                self.redis_client = redis.from_url(settings.redis_url)
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Using in-memory cache.")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        # Try Redis first
        if self.redis_client:
            try:
                value = await self.redis_client.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.warning(f"Redis get error: {e}")
        
        # Fallback to memory cache
        if key in self.memory_cache:
            cached_data, expiry = self.memory_cache[key]
            if datetime.now() < expiry:
                return cached_data
            else:
                del self.memory_cache[key]
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        ttl = ttl or settings.cache_ttl_seconds
        
        # Try Redis first
        if self.redis_client:
            try:
                await self.redis_client.setex(key, ttl, json.dumps(value))
                return True
            except Exception as e:
                logger.warning(f"Redis set error: {e}")
        
        # Fallback to memory cache
        expiry = datetime.now() + timedelta(seconds=ttl)
        self.memory_cache[key] = (value, expiry)
        
        # Clean expired entries periodically
        if len(self.memory_cache) > 1000:  # Arbitrary limit
            await self._clean_expired()
        
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        # Try Redis first
        if self.redis_client:
            try:
                await self.redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Redis delete error: {e}")
        
        # Remove from memory cache
        if key in self.memory_cache:
            del self.memory_cache[key]
        
        return True
    
    async def _clean_expired(self):
        """Clean expired entries from memory cache"""
        now = datetime.now()
        expired_keys = [
            key for key, (_, expiry) in self.memory_cache.items()
            if now >= expiry
        ]
        for key in expired_keys:
            del self.memory_cache[key]


# Global cache instance
cache_manager = CacheManager()
