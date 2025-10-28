from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings


class APIKeyAuth(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(APIKeyAuth, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> str:
        # Check for API key in X-API-Key header
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            # Fallback to Authorization header
            credentials: HTTPAuthorizationCredentials = await super(APIKeyAuth, self).__call__(request)
            if not credentials:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API key required. Provide X-API-Key header or Authorization Bearer token."
                )
            api_key = credentials.credentials
        
        if api_key not in settings.parsed_api_keys:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        return api_key


# Global auth instance
auth_scheme = APIKeyAuth()

