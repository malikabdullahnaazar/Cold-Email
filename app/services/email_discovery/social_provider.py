import asyncio
import re
from typing import List, Set
import httpx
from bs4 import BeautifulSoup
from app.services.email_discovery.base import EmailDiscoveryProvider
from app.models.responses import EmailResult
from app.config import settings
from app.utils.logger import logger


class SocialProvider(EmailDiscoveryProvider):
    """Email discovery using social media platforms"""
    
    def __init__(self):
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        self.timeout = 15
    
    async def discover(self, domain: str) -> List[EmailResult]:
        """Discover emails from social media platforms"""
        if not self.is_available():
            return []
        
        emails = set()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Search LinkedIn company page
                linkedin_emails = await self._search_linkedin(client, domain)
                emails.update(linkedin_emails)
                
                # Search Twitter/X company profile
                twitter_emails = await self._search_twitter(client, domain)
                emails.update(twitter_emails)
        
        except Exception as e:
            logger.warning(f"Social media discovery failed for {domain}: {e}")
        
        return [
            EmailResult(
                email=email,
                source="social_media",
                confidence=0.7,  # Medium confidence
                found_at=f"social:{domain}"
            )
            for email in emails
        ]
    
    async def _search_linkedin(self, client: httpx.AsyncClient, domain: str) -> Set[str]:
        """Search LinkedIn for company emails"""
        emails = set()
        
        try:
            # Try to find LinkedIn company page
            search_urls = [
                f"https://www.linkedin.com/company/{domain}",
                f"https://www.linkedin.com/company/{domain.replace('.com', '')}",
                f"https://www.linkedin.com/company/{domain.replace('.com', '').replace('.', '-')}"
            ]
            
            for url in search_urls:
                try:
                    response = await client.get(url, follow_redirects=True)
                    if response.status_code == 200:
                        page_emails = self._extract_emails_from_page(response.text, domain)
                        emails.update(page_emails)
                        break
                except Exception as e:
                    logger.debug(f"LinkedIn search failed for {url}: {e}")
                    continue
        
        except Exception as e:
            logger.debug(f"LinkedIn discovery failed for {domain}: {e}")
        
        return emails
    
    async def _search_twitter(self, client: httpx.AsyncClient, domain: str) -> Set[str]:
        """Search Twitter/X for company emails"""
        emails = set()
        
        try:
            # Try to find Twitter company profile
            search_urls = [
                f"https://twitter.com/{domain}",
                f"https://twitter.com/{domain.replace('.com', '')}",
                f"https://x.com/{domain}",
                f"https://x.com/{domain.replace('.com', '')}"
            ]
            
            for url in search_urls:
                try:
                    response = await client.get(url, follow_redirects=True)
                    if response.status_code == 200:
                        page_emails = self._extract_emails_from_page(response.text, domain)
                        emails.update(page_emails)
                        break
                except Exception as e:
                    logger.debug(f"Twitter search failed for {url}: {e}")
                    continue
        
        except Exception as e:
            logger.debug(f"Twitter discovery failed for {domain}: {e}")
        
        return emails
    
    def _extract_emails_from_page(self, html_content: str, domain: str) -> Set[str]:
        """Extract emails from HTML content"""
        emails = set()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find emails in text content
            text_content = soup.get_text()
            found_emails = self.email_pattern.findall(text_content)
            
            # Find emails in meta tags
            meta_tags = soup.find_all('meta')
            for meta in meta_tags:
                content = meta.get('content', '')
                if content:
                    meta_emails = self.email_pattern.findall(content)
                    found_emails.extend(meta_emails)
            
            # Find emails in href attributes
            links = soup.find_all('a', href=True)
            for link in links:
                href = link['href']
                if href.startswith('mailto:'):
                    email = href[7:]  # Remove 'mailto:' prefix
                    found_emails.append(email)
            
            # Filter emails for the target domain
            for email in found_emails:
                email_lower = email.lower()
                if email_lower.endswith(f"@{domain.lower()}"):
                    emails.add(email_lower)
        
        except Exception as e:
            logger.debug(f"Failed to extract emails from page: {e}")
        
        return emails
    
    def is_available(self) -> bool:
        return settings.enable_social_scraping
    
    def get_name(self) -> str:
        return "social_media"
