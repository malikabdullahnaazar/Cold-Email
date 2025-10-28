import re
from email_validator import validate_email, EmailNotValidError
from app.models.responses import ValidationResult


class SyntaxValidator:
    """Email syntax validation"""
    
    def __init__(self):
        # Basic regex pattern for additional validation
        self.email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
    
    async def validate(self, email: str) -> ValidationResult:
        """Validate email syntax"""
        try:
            # Use email-validator library for comprehensive validation
            # Disable deliverability checking to avoid DNS issues in syntax validation
            validated_email = validate_email(email, check_deliverability=False)
            normalized_email = validated_email.email
            
            return ValidationResult(
                valid=True,
                message="Email syntax is valid",
                details={
                    "normalized_email": normalized_email,
                    "local_part": validated_email.local,
                    "domain": validated_email.domain
                }
            )
        
        except EmailNotValidError as e:
            return ValidationResult(
                valid=False,
                message=f"Email syntax is invalid: {str(e)}",
                details={"error_type": "syntax_error"}
            )
        
        except Exception as e:
            return ValidationResult(
                valid=False,
                message=f"Email validation failed: {str(e)}",
                details={"error_type": "validation_error"}
            )

