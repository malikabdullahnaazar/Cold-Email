import asyncio
import hashlib
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.models.requests import EmailDiscoveryRequest
from app.models.responses import EmailDiscoveryResponse, ErrorResponse
from app.middleware.auth_middleware import auth_scheme
from app.middleware.rate_limiter import check_rate_limit
from app.services.email_discovery.scraper import WebScrapingProvider
from app.services.email_discovery.pattern_matcher import PatternMatchingProvider
from app.services.email_discovery.third_party.hunter_io import HunterIOProvider
from app.services.email_discovery.whois_provider import WHOISProvider
from app.services.email_discovery.github_provider import GitHubProvider
from app.services.email_discovery.social_provider import SocialProvider
from app.utils.cache import cache_manager
from app.utils.logger import logger

router = APIRouter(prefix="/api/v1", tags=["discovery"])

# Initialize providers
providers = {
    "scraping": WebScrapingProvider(),
    "patterns": PatternMatchingProvider(),
    "third_party": HunterIOProvider(),
    "whois": WHOISProvider(),
    "github": GitHubProvider(),
    "social": SocialProvider()
}


@router.post(
    "/discover",
    response_model=EmailDiscoveryResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        429: {"model": ErrorResponse, "description": "Rate Limit Exceeded"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
async def discover_emails(
    request: EmailDiscoveryRequest,
    http_request: Request,
    api_key: str = Depends(auth_scheme)
):
    """
    Discover email addresses for a given domain using various methods.
    
    - **domain**: Domain name to search for emails
    - **methods**: List of discovery methods to use (scraping, patterns, third_party)
    - **detailed**: Whether to return detailed response with metadata
    """
    # Check rate limit
    check_rate_limit(http_request, api_key)
    
    # Generate cache key
    cache_key = f"discovery:{hashlib.md5(f'{request.domain}:{sorted(request.methods)}'.encode()).hexdigest()}"
    
    # Check cache
    cached_result = await cache_manager.get(cache_key)
    if cached_result:
        logger.info(f"Cache hit for domain: {request.domain}")
        return EmailDiscoveryResponse(**cached_result)
    
    try:
        all_emails = []
        methods_used = []
        
        # Run discovery methods concurrently
        tasks = []
        for method in request.methods:
            if method in providers and providers[method].is_available():
                tasks.append(providers[method].discover(request.domain))
                methods_used.append(method)
        
        if not tasks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid discovery methods available"
            )
        
        # Execute all discovery methods
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Discovery method {methods_used[i]} failed: {result}")
                continue
            
            all_emails.extend(result)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_emails = []
        for email_result in all_emails:
            if email_result.email not in seen:
                seen.add(email_result.email)
                unique_emails.append(email_result)
        
        # Prepare response
        response_data = {
            "domain": request.domain,
            "emails": [email.dict() for email in unique_emails],
            "total_found": len(unique_emails),
            "cached": False,
            "methods_used": methods_used
        }
        
        # Cache the result
        await cache_manager.set(cache_key, response_data)
        
        logger.info(f"Discovered {len(unique_emails)} emails for {request.domain}")
        return EmailDiscoveryResponse(**response_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email discovery failed for {request.domain}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email discovery failed"
        )


@router.get("/providers/status")
async def get_providers_status():
    """
    Get status of all email discovery providers.
    
    Returns information about which providers are available and their capabilities.
    """
    provider_status = {}
    
    for name, provider in providers.items():
        provider_status[name] = {
            "available": provider.is_available(),
            "name": provider.get_name(),
            "description": _get_provider_description(name)
        }
    
    return {
        "providers": provider_status,
        "total_providers": len(providers),
        "available_providers": sum(1 for p in providers.values() if p.is_available())
    }


def _get_provider_description(provider_name: str) -> str:
    """Get human-readable description for provider"""
    descriptions = {
        "scraping": "Web scraping from company websites (contact, about, team pages)",
        "patterns": "Common email patterns (info@, contact@, admin@, etc.)",
        "third_party": "Hunter.io API integration (requires API key)",
        "whois": "Domain registration emails from WHOIS data",
        "github": "GitHub organization member emails and repository contributors",
        "social": "Social media platform emails (LinkedIn, Twitter/X)"
    }
    return descriptions.get(provider_name, "Unknown provider")
