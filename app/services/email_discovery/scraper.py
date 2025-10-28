import re
import asyncio
from typing import List, Set, Dict
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup
from app.services.email_discovery.base import EmailDiscoveryProvider
from app.models.responses import EmailResult
from app.utils.logger import logger


class WebScrapingProvider(EmailDiscoveryProvider):
    """Email discovery through web scraping"""
    
    def __init__(self, max_pages: int = 10, timeout: int = 10):
        self.max_pages = max_pages
        self.timeout = timeout
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        
        # Targeted pages with confidence scores
        self.targeted_pages = {
            '/contact': 0.95,
            '/contact-us': 0.95,
            '/about': 0.85,
            '/about-us': 0.85,
            '/team': 0.90,
            '/people': 0.90,
            '/staff': 0.90,
            '/careers': 0.80,
            '/jobs': 0.80,
            '/leadership': 0.85,
            '/management': 0.85,
            '/press': 0.75,
            '/media': 0.75,
            '/support': 0.80,
            '/help': 0.80
        }
        
        # Semaphore for rate limiting
        self.semaphore = asyncio.Semaphore(3)
    
    async def discover(self, domain: str) -> List[EmailResult]:
        """Discover emails by scraping the domain's website"""
        email_results = []
        base_url = f"https://{domain}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Get main page
                main_emails = await self._scrape_page_with_confidence(client, base_url, domain, 0.8)
                email_results.extend(main_emails)
                
                # Get targeted pages first
                targeted_urls = await self._get_targeted_pages(client, base_url, domain)
                for url, confidence in targeted_urls:
                    page_emails = await self._scrape_page_with_confidence(client, url, domain, confidence)
                    email_results.extend(page_emails)
                
                # Get additional pages if we haven't reached max_pages
                if len(targeted_urls) < self.max_pages - 1:
                    additional_urls = await self._find_additional_pages(client, base_url, domain)
                    remaining_pages = self.max_pages - 1 - len(targeted_urls)
                    for url in additional_urls[:remaining_pages]:
                        page_emails = await self._scrape_page_with_confidence(client, url, domain, 0.6)
                        email_results.extend(page_emails)
        
        except Exception as e:
            logger.warning(f"Web scraping failed for {domain}: {e}")
        
        # Remove duplicates while preserving highest confidence
        unique_emails = {}
        for email_result in email_results:
            email = email_result.email
            if email not in unique_emails or email_result.confidence > unique_emails[email].confidence:
                unique_emails[email] = email_result
        
        return list(unique_emails.values())
    
    async def _get_targeted_pages(self, client: httpx.AsyncClient, base_url: str, domain: str) -> List[tuple]:
        """Get targeted pages with their confidence scores"""
        targeted_urls = []
        
        for path, confidence in self.targeted_pages.items():
            url = f"{base_url}{path}"
            try:
                async with self.semaphore:
                    response = await client.head(url)
                    if response.status_code == 200:
                        targeted_urls.append((url, confidence))
            except Exception as e:
                logger.debug(f"Failed to check {url}: {e}")
                continue
        
        return targeted_urls
    
    async def _scrape_page_with_confidence(self, client: httpx.AsyncClient, url: str, domain: str, confidence: float) -> List[EmailResult]:
        """Scrape a single page for emails with confidence scoring"""
        emails = []
        
        try:
            async with self.semaphore:
                response = await client.get(url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract emails from various sources
                page_emails = self._extract_emails_from_soup(soup, domain)
                
                for email in page_emails:
                    emails.append(EmailResult(
                        email=email,
                        source="web_scraping",
                        confidence=confidence,
                        found_at=url
                    ))
        
        except Exception as e:
            logger.debug(f"Failed to scrape {url}: {e}")
        
        return emails
    
    def _extract_emails_from_soup(self, soup: BeautifulSoup, domain: str) -> Set[str]:
        """Extract emails from BeautifulSoup object"""
        emails = set()
        
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
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('mailto:'):
                email = href[7:]  # Remove 'mailto:' prefix
                found_emails.append(email)
        
        # Filter emails for the target domain
        for email in found_emails:
            if email.lower().endswith(f"@{domain.lower()}"):
                emails.add(email.lower())
        
        return emails
    
    async def _scrape_page(self, client: httpx.AsyncClient, url: str, domain: str) -> Set[str]:
        """Scrape a single page for emails"""
        emails = set()
        
        try:
            response = await client.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find emails in text content
            text_content = soup.get_text()
            found_emails = self.email_pattern.findall(text_content)
            
            # Filter emails for the target domain
            for email in found_emails:
                if email.lower().endswith(f"@{domain.lower()}"):
                    emails.add(email.lower())
            
            # Find emails in href attributes
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('mailto:'):
                    email = href[7:]  # Remove 'mailto:' prefix
                    if email.lower().endswith(f"@{domain.lower()}"):
                        emails.add(email.lower())
        
        except Exception as e:
            logger.warning(f"Failed to scrape {url}: {e}")
        
        return emails
    
    async def _find_additional_pages(self, client: httpx.AsyncClient, base_url: str, domain: str) -> List[str]:
        """Find additional pages to scrape"""
        urls = set()
        
        try:
            response = await client.get(base_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find internal links
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(base_url, href)
                parsed = urlparse(full_url)
                
                # Only include same domain links
                if parsed.netloc == domain or parsed.netloc == f"www.{domain}":
                    urls.add(full_url)
        
        except Exception as e:
            logger.warning(f"Failed to find additional pages for {domain}: {e}")
        
        return list(urls)
    
    def is_available(self) -> bool:
        return True
    
    def get_name(self) -> str:
        return "web_scraping"

