from typing import List, Optional, Literal
from pydantic import BaseModel, EmailStr, Field


class EmailDiscoveryRequest(BaseModel):
    domain: str = Field(..., description="Domain name to discover emails from", example="falconxoft.com")
    methods: List[str] = Field(
        default=["scraping", "patterns", "whois", "github", "social"], 
        description="Discovery methods to use",
        example=["scraping", "patterns", "whois", "github", "social", "third_party"]
    )
    detailed: bool = Field(default=True, description="Return detailed response with metadata")


class EmailValidationRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address to validate", example="abc@falconxoft.com")
    validation_level: Literal["basic", "advanced"] = Field(
        default="advanced", 
        description="Validation level: basic (syntax + DNS) or advanced (syntax + DNS + SMTP)"
    )
    detailed: bool = Field(default=True, description="Return detailed response with validation results")

