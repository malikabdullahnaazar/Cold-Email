import asyncio
import whois
import re
from typing import List, Set
from app.services.email_discovery.base import EmailDiscoveryProvider
from app.models.responses import EmailResult
from app.config import settings
from app.utils.logger import logger


class WHOISProvider(EmailDiscoveryProvider):
    """Email discovery using WHOIS data"""
    
    def __init__(self):
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        # Common privacy protection services
        self.privacy_services = {
            'whoisguard', 'whoisguard.com', 'whoisguard.net',
            'domainsbyproxy', 'domainsbyproxy.com',
            'privacyprotect', 'privacyprotect.org',
            'namecheap', 'namecheap.com',
            'godaddy', 'godaddy.com',
            'enom', 'enom.com',
            'tucows', 'tucows.com',
            'privacy', 'privacy.org',
            'redacted', 'redacted.com',
            'protected', 'protected.com'
        }
    
    async def discover(self, domain: str) -> List[EmailResult]:
        """Discover emails from WHOIS data"""
        if not self.is_available():
            return []
        
        emails = set()
        
        try:
            # Run WHOIS lookup in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            whois_data = await loop.run_in_executor(None, self._get_whois_data, domain)
            
            if whois_data:
                # Extract emails from various WHOIS fields
                whois_emails = self._extract_emails_from_whois(whois_data, domain)
                emails.update(whois_emails)
        
        except Exception as e:
            logger.warning(f"WHOIS lookup failed for {domain}: {e}")
        
        return [
            EmailResult(
                email=email,
                source="whois",
                confidence=0.85,  # High confidence for WHOIS data
                found_at=f"whois:{domain}"
            )
            for email in emails
        ]
    
    def _get_whois_data(self, domain: str):
        """Get WHOIS data synchronously"""
        try:
            return whois.whois(domain)
        except Exception as e:
            logger.debug(f"WHOIS query failed for {domain}: {e}")
            return None
    
    def _extract_emails_from_whois(self, whois_data, domain: str) -> Set[str]:
        """Extract emails from WHOIS data"""
        emails = set()
        
        # Fields to check for emails
        email_fields = [
            'emails', 'email', 'admin_email', 'tech_email', 'registrant_email',
            'registrar_email', 'billing_email', 'abuse_email', 'zone_email'
        ]
        
        for field in email_fields:
            if hasattr(whois_data, field):
                value = getattr(whois_data, field)
                if value:
                    if isinstance(value, list):
                        for item in value:
                            if isinstance(item, str):
                                found_emails = self._extract_emails_from_text(item, domain)
                                emails.update(found_emails)
                    elif isinstance(value, str):
                        found_emails = self._extract_emails_from_text(value, domain)
                        emails.update(found_emails)
        
        # Check all string attributes for email patterns
        for attr_name in dir(whois_data):
            if not attr_name.startswith('_'):
                try:
                    attr_value = getattr(whois_data, attr_name)
                    if isinstance(attr_value, str):
                        found_emails = self._extract_emails_from_text(attr_value, domain)
                        emails.update(found_emails)
                except:
                    continue
        
        return emails
    
    def _extract_emails_from_text(self, text: str, domain: str) -> Set[str]:
        """Extract emails from text and filter for target domain"""
        if not text:
            return set()
        
        emails = set()
        found_emails = self.email_pattern.findall(text)
        
        for email in found_emails:
            email_lower = email.lower()
            domain_lower = domain.lower()
            
            # Check if email is for the target domain
            if email_lower.endswith(f"@{domain_lower}"):
                # Filter out privacy protection services
                if not self._is_privacy_protected(email_lower):
                    emails.add(email_lower)
        
        return emails
    
    def _is_privacy_protected(self, email: str) -> bool:
        """Check if email is from a privacy protection service"""
        email_domain = email.split('@')[1].lower()
        return email_domain in self.privacy_services
    
    def is_available(self) -> bool:
        return settings.enable_whois
    
    def get_name(self) -> str:
        return "whois"
