import os
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Configuration
    api_keys: Optional[str] = None
    rate_limit_per_minute: int = 10
    cache_ttl_seconds: int = 3600
    
    # Redis Configuration
    redis_url: Optional[str] = None
    
    # SMTP Configuration
    smtp_timeout: int = 10
    smtp_max_retries: int = 3
    
    # Third-party Integration - Disabled by default
    enable_third_party: bool = False
    hunter_io_api_key: Optional[str] = None
    snov_io_api_key: Optional[str] = None
    
    # Free Discovery Providers
    enable_whois: bool = True
    enable_github: bool = True
    enable_social_scraping: bool = True
    github_token: Optional[str] = None
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
    @property
    def parsed_api_keys(self) -> List[str]:
        """Parse comma-separated API keys into a list"""
        if not self.api_keys:
            return []
        return [key.strip() for key in self.api_keys.split(",") if key.strip()]


settings = Settings()

