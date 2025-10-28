import httpx
from typing import List
from app.services.email_discovery.base import EmailDiscoveryProvider
from app.models.responses import EmailResult
from app.config import settings
from app.utils.logger import logger


class HunterIOProvider(EmailDiscoveryProvider):
    """Email discovery using Hunter.io API"""
    
    def __init__(self):
        self.api_key = settings.hunter_io_api_key
        self.base_url = "https://api.hunter.io/v2"
    
    async def discover(self, domain: str) -> List[EmailResult]:
        """Discover emails using Hunter.io API"""
        if not self.is_available():
            return []
        
        emails = []
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                url = f"{self.base_url}/domain-search"
                params = {
                    "domain": domain,
                    "api_key": self.api_key,
                    "limit": 100
                }
                
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if "data" in data and "emails" in data["data"]:
                    for email_data in data["data"]["emails"]:
                        emails.append(EmailResult(
                            email=email_data["value"],
                            source="hunter_io",
                            confidence=email_data.get("confidence", 0.5) / 100,  # Convert to 0-1 scale
                            found_at=None
                        ))
        
        except Exception as e:
            logger.warning(f"Hunter.io API failed for {domain}: {e}")
        
        return emails
    
    def is_available(self) -> bool:
        return bool(self.api_key and settings.enable_third_party)
    
    def get_name(self) -> str:
        return "hunter_io"

