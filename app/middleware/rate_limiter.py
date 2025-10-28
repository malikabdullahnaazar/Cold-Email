import time
from typing import Dict, Optional
from fastapi import Request, HTTPException, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.config import settings


# Rate limiter with Redis support if available
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"]
)


def get_rate_limit_key(request: Request) -> str:
    """Generate rate limit key based on API key if available"""
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"rate_limit:{api_key}"
    return get_remote_address(request)


# Custom rate limiter for API key-based limiting
class APIKeyRateLimiter:
    def __init__(self):
        self.requests: Dict[str, list] = {}
    
    def is_allowed(self, api_key: str) -> bool:
        """Check if API key is within rate limit"""
        now = time.time()
        minute_ago = now - 60
        
        if api_key not in self.requests:
            self.requests[api_key] = []
        
        # Clean old requests
        self.requests[api_key] = [
            req_time for req_time in self.requests[api_key]
            if req_time > minute_ago
        ]
        
        # Check if under limit
        if len(self.requests[api_key]) >= settings.rate_limit_per_minute:
            return False
        
        # Add current request
        self.requests[api_key].append(now)
        return True


# Global rate limiter instance
api_key_rate_limiter = APIKeyRateLimiter()


def check_rate_limit(request: Request, api_key: str):
    """Check rate limit for API key"""
    if not api_key_rate_limiter.is_allowed(api_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {settings.rate_limit_per_minute} requests per minute."
        )

