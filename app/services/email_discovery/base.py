from abc import ABC, abstractmethod
from typing import List
from app.models.responses import EmailResult


class EmailDiscoveryProvider(ABC):
    """Abstract base class for email discovery providers"""
    
    @abstractmethod
    async def discover(self, domain: str) -> List[EmailResult]:
        """Discover emails for a domain"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get provider name"""
        pass

