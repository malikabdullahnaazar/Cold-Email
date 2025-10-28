from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class EmailResult(BaseModel):
    email: str = Field(..., description="Discovered email address")
    source: str = Field(..., description="Source of the email (web_scraping, common_pattern, third_party)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    found_at: Optional[str] = Field(None, description="URL where email was found (for web scraping)")


class EmailDiscoveryResponse(BaseModel):
    domain: str = Field(..., description="Domain that was searched")
    emails: List[EmailResult] = Field(..., description="List of discovered emails")
    total_found: int = Field(..., description="Total number of emails found")
    cached: bool = Field(..., description="Whether result was served from cache")
    methods_used: List[str] = Field(..., description="Discovery methods that were used")


class ValidationResult(BaseModel):
    valid: bool = Field(..., description="Whether validation passed")
    message: str = Field(..., description="Validation message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional validation details")
    is_catch_all: Optional[bool] = Field(None, description="Whether domain uses catch-all email")
    email_provider: Optional[str] = Field(None, description="Email provider (Gmail, custom, etc.)")
    is_disposable: bool = Field(default=False, description="Whether email is from disposable service")


class EmailValidationResponse(BaseModel):
    email: str = Field(..., description="Email that was validated")
    valid: bool = Field(..., description="Overall validation result")
    validation_results: Optional[Dict[str, ValidationResult]] = Field(
        None, 
        description="Detailed validation results for each check"
    )
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Risk score (0-1, lower is better)")
    cached: bool = Field(..., description="Whether result was served from cache")


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")
    status_code: int = Field(..., description="HTTP status code")

