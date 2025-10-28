import asyncio
import re
from typing import List, Set
import httpx
from app.services.email_discovery.base import EmailDiscoveryProvider
from app.models.responses import EmailResult
from app.config import settings
from app.utils.logger import logger


class GitHubProvider(EmailDiscoveryProvider):
    """Email discovery using GitHub organization data"""
    
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "EmailDiscovery/1.0"
        }
        if settings.github_token:
            self.headers["Authorization"] = f"token {settings.github_token}"
    
    async def discover(self, domain: str) -> List[EmailResult]:
        """Discover emails from GitHub organization"""
        if not self.is_available():
            return []
        
        emails = set()
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Search for organization
                org_data = await self._search_organization(client, domain)
                if org_data:
                    # Get organization members
                    member_emails = await self._get_organization_members(client, org_data["login"])
                    emails.update(member_emails)
                    
                    # Get organization repositories
                    repo_emails = await self._get_repository_emails(client, org_data["login"])
                    emails.update(repo_emails)
        
        except Exception as e:
            logger.warning(f"GitHub discovery failed for {domain}: {e}")
        
        return [
            EmailResult(
                email=email,
                source="github",
                confidence=0.75,  # Medium-high confidence
                found_at=f"github:{domain}"
            )
            for email in emails
        ]
    
    async def _search_organization(self, client: httpx.AsyncClient, domain: str) -> dict:
        """Search for GitHub organization by domain"""
        try:
            # Try exact domain match first
            url = f"{self.base_url}/orgs/{domain}"
            response = await client.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return response.json()
            
            # If not found, search for organizations
            search_url = f"{self.base_url}/search/users"
            params = {
                "q": f"type:org {domain}",
                "per_page": 5
            }
            
            response = await client.get(search_url, params=params, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            if data.get("items"):
                # Return first match
                return data["items"][0]
        
        except Exception as e:
            logger.debug(f"GitHub organization search failed for {domain}: {e}")
        
        return None
    
    async def _get_organization_members(self, client: httpx.AsyncClient, org_login: str) -> Set[str]:
        """Get emails from organization members"""
        emails = set()
        
        try:
            url = f"{self.base_url}/orgs/{org_login}/members"
            params = {"per_page": 100}
            
            response = await client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            
            members = response.json()
            
            # Get public emails from member profiles
            for member in members[:10]:  # Limit to first 10 members
                try:
                    user_url = f"{self.base_url}/users/{member['login']}"
                    user_response = await client.get(user_url, headers=self.headers)
                    
                    if user_response.status_code == 200:
                        user_data = user_response.json()
                        if user_data.get("email"):
                            email = user_data["email"].lower()
                            if self._is_valid_company_email(email, org_login):
                                emails.add(email)
                except Exception as e:
                    logger.debug(f"Failed to get user data for {member['login']}: {e}")
                    continue
        
        except Exception as e:
            logger.debug(f"Failed to get organization members for {org_login}: {e}")
        
        return emails
    
    async def _get_repository_emails(self, client: httpx.AsyncClient, org_login: str) -> Set[str]:
        """Get emails from organization repositories"""
        emails = set()
        
        try:
            # Get organization repositories
            url = f"{self.base_url}/orgs/{org_login}/repos"
            params = {"per_page": 20, "sort": "updated"}
            
            response = await client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            
            repos = response.json()
            
            for repo in repos[:5]:  # Limit to first 5 repos
                try:
                    # Get README content
                    readme_emails = await self._get_readme_emails(client, org_login, repo["name"])
                    emails.update(readme_emails)
                    
                    # Get CONTRIBUTORS file
                    contributors_emails = await self._get_contributors_emails(client, org_login, repo["name"])
                    emails.update(contributors_emails)
                    
                except Exception as e:
                    logger.debug(f"Failed to process repo {repo['name']}: {e}")
                    continue
        
        except Exception as e:
            logger.debug(f"Failed to get repositories for {org_login}: {e}")
        
        return emails
    
    async def _get_readme_emails(self, client: httpx.AsyncClient, org: str, repo: str) -> Set[str]:
        """Extract emails from README content"""
        emails = set()
        
        try:
            url = f"{self.base_url}/repos/{org}/{repo}/readme"
            response = await client.get(url, headers=self.headers)
            
            if response.status_code == 200:
                readme_data = response.json()
                if readme_data.get("content"):
                    import base64
                    content = base64.b64decode(readme_data["content"]).decode("utf-8")
                    found_emails = self.email_pattern.findall(content)
                    
                    for email in found_emails:
                        email_lower = email.lower()
                        if self._is_valid_company_email(email_lower, org):
                            emails.add(email_lower)
        
        except Exception as e:
            logger.debug(f"Failed to get README for {org}/{repo}: {e}")
        
        return emails
    
    async def _get_contributors_emails(self, client: httpx.AsyncClient, org: str, repo: str) -> Set[str]:
        """Extract emails from CONTRIBUTORS file"""
        emails = set()
        
        try:
            url = f"{self.base_url}/repos/{org}/{repo}/contents/CONTRIBUTORS"
            response = await client.get(url, headers=self.headers)
            
            if response.status_code == 200:
                contributors_data = response.json()
                if contributors_data.get("content"):
                    import base64
                    content = base64.b64decode(contributors_data["content"]).decode("utf-8")
                    found_emails = self.email_pattern.findall(content)
                    
                    for email in found_emails:
                        email_lower = email.lower()
                        if self._is_valid_company_email(email_lower, org):
                            emails.add(email_lower)
        
        except Exception as e:
            logger.debug(f"Failed to get CONTRIBUTORS for {org}/{repo}: {e}")
        
        return emails
    
    def _is_valid_company_email(self, email: str, org: str) -> bool:
        """Check if email is likely a company email"""
        # Skip common personal email providers
        personal_domains = {
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
            'aol.com', 'icloud.com', 'protonmail.com', 'yandex.com'
        }
        
        email_domain = email.split('@')[1].lower()
        
        # Skip personal email domains
        if email_domain in personal_domains:
            return False
        
        # Check if email domain matches organization name
        org_clean = org.lower().replace('-', '').replace('_', '')
        domain_clean = email_domain.replace('.com', '').replace('.org', '').replace('.net', '')
        
        return org_clean in domain_clean or domain_clean in org_clean
    
    def is_available(self) -> bool:
        return settings.enable_github
    
    def get_name(self) -> str:
        return "github"
