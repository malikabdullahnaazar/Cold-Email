import asyncio
import hashlib
from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.models.requests import EmailValidationRequest
from app.models.responses import EmailValidationResponse, ErrorResponse, ValidationResult
from app.middleware.auth_middleware import auth_scheme
from app.middleware.rate_limiter import check_rate_limit
from app.services.email_validation.syntax_validator import SyntaxValidator
from app.services.email_validation.dns_validator import DNSValidator
from app.services.email_validation.smtp_validator import SMTPValidator
from app.utils.cache import cache_manager
from app.utils.logger import logger

router = APIRouter(prefix="/api/v1", tags=["validation"])

# Initialize validators
syntax_validator = SyntaxValidator()
dns_validator = DNSValidator()
smtp_validator = SMTPValidator()


@router.post(
    "/validate",
    response_model=EmailValidationResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        429: {"model": ErrorResponse, "description": "Rate Limit Exceeded"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
async def validate_email(
    request: EmailValidationRequest,
    http_request: Request,
    api_key: str = Depends(auth_scheme)
):
    """
    Validate an email address using various validation methods.
    
    - **email**: Email address to validate
    - **validation_level**: Validation level (basic or advanced)
    - **detailed**: Whether to return detailed validation results
    """
    # Check rate limit
    check_rate_limit(http_request, api_key)
    
    # Generate cache key
    cache_key = f"validation:{hashlib.md5(f'{request.email}:{request.validation_level}'.encode()).hexdigest()}"
    
    # Check cache
    cached_result = await cache_manager.get(cache_key)
    if cached_result:
        logger.info(f"Cache hit for email: {request.email}")
        return EmailValidationResponse(**cached_result)
    
    try:
        validation_results = {}
        overall_valid = True
        risk_score = 0.0
        
        # 1. Syntax validation (always performed)
        syntax_result = await syntax_validator.validate(str(request.email))
        validation_results["syntax"] = syntax_result
        if not syntax_result.valid:
            overall_valid = False
            risk_score += 0.5
        
        # 2. DNS validation (always performed)
        dns_result = await dns_validator.validate(str(request.email))
        validation_results["dns"] = dns_result
        if not dns_result.valid:
            overall_valid = False
            risk_score += 0.3
        
        # 3. SMTP validation (only for advanced level)
        if request.validation_level == "advanced" and dns_result.valid:
            # Extract MX records from DNS result
            mx_records = dns_result.details.get("mx_records", []) if dns_result.details else []
            smtp_result = await smtp_validator.validate(str(request.email), mx_records)
            validation_results["smtp"] = smtp_result
            if not smtp_result.valid:
                overall_valid = False
                risk_score += 0.2
        
        # Calculate final risk score (0-1, lower is better)
        risk_score = min(risk_score, 1.0)
        
        # Prepare response
        response_data = {
            "email": str(request.email),
            "valid": overall_valid,
            "validation_results": validation_results if request.detailed else None,
            "risk_score": risk_score,
            "cached": False
        }
        
        # Cache the result
        await cache_manager.set(cache_key, response_data)
        
        logger.info(f"Validated email {request.email}: valid={overall_valid}, risk_score={risk_score}")
        return EmailValidationResponse(**response_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email validation failed for {request.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email validation failed"
        )

