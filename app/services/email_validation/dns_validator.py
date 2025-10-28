import dns.resolver
import dns.exception
from typing import List, Dict, Any
from app.models.responses import ValidationResult
from app.utils.logger import logger


class DNSValidator:
    """DNS and MX record validation"""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        
        # Email provider patterns
        self.provider_patterns = {
            'gmail.com': 'Gmail',
            'googlemail.com': 'Gmail',
            'outlook.com': 'Outlook',
            'hotmail.com': 'Outlook',
            'live.com': 'Outlook',
            'yahoo.com': 'Yahoo',
            'yahoo.co.uk': 'Yahoo',
            'yahoo.ca': 'Yahoo',
            'aol.com': 'AOL',
            'icloud.com': 'iCloud',
            'me.com': 'iCloud',
            'mac.com': 'iCloud',
            'protonmail.com': 'ProtonMail',
            'yandex.com': 'Yandex',
            'yandex.ru': 'Yandex',
            'zoho.com': 'Zoho',
            'fastmail.com': 'Fastmail',
            'tutanota.com': 'Tutanota'
        }
        
        # Business email provider patterns
        self.business_providers = {
            'google.com': 'Google Workspace',
            'microsoft.com': 'Microsoft 365',
            'office365.com': 'Microsoft 365',
            'outlook.office365.com': 'Microsoft 365',
            'amazonaws.com': 'Amazon SES',
            'sendgrid.net': 'SendGrid',
            'mailgun.org': 'Mailgun',
            'postmarkapp.com': 'Postmark',
            'mandrillapp.com': 'Mandrill',
            'mailchimp.com': 'Mailchimp'
        }
    
    async def validate(self, email: str) -> ValidationResult:
        """Validate domain DNS and MX records"""
        try:
            domain = email.split('@')[1]
            
            # Create resolver with timeout
            resolver = dns.resolver.Resolver()
            resolver.timeout = self.timeout
            resolver.lifetime = self.timeout
            
            # Check if domain exists
            try:
                resolver.resolve(domain, 'A')
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                return ValidationResult(
                    valid=False,
                    message="Domain does not exist",
                    details={"error_type": "domain_not_found"}
                )
            
            # Check MX records
            try:
                mx_records = resolver.resolve(domain, 'MX')
                mx_list = [str(mx.exchange).rstrip('.') for mx in mx_records]
                
                if not mx_list:
                    return ValidationResult(
                        valid=False,
                        message="Domain has no MX records",
                        details={"error_type": "no_mx_records"}
                    )
                
                # Analyze MX records for provider detection
                provider_info = self._analyze_mx_records(mx_list)
                
                return ValidationResult(
                    valid=True,
                    message="Domain has valid MX records",
                    details={
                        "mx_records": mx_list,
                        "mx_count": len(mx_list),
                        "provider_info": provider_info
                    },
                    email_provider=provider_info.get('provider_type', 'Custom')
                )
            
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                return ValidationResult(
                    valid=False,
                    message="Domain has no MX records",
                    details={"error_type": "no_mx_records"}
                )
        
        except dns.exception.Timeout:
            return ValidationResult(
                valid=False,
                message="DNS lookup timeout",
                details={"error_type": "dns_timeout"}
            )
        
        except Exception as e:
            logger.warning(f"DNS validation failed for {email}: {e}")
            return ValidationResult(
                valid=False,
                message=f"DNS validation failed: {str(e)}",
                details={"error_type": "dns_error"}
            )
    
    def _analyze_mx_records(self, mx_records: List[str]) -> Dict[str, Any]:
        """Analyze MX records to detect email provider"""
        provider_info = {
            'provider_type': 'Custom',
            'is_business': False,
            'is_free': False,
            'provider_name': 'Unknown'
        }
        
        # Check for free email providers
        for mx_record in mx_records:
            mx_lower = mx_record.lower()
            
            # Check for free email providers
            for domain, provider in self.provider_patterns.items():
                if domain in mx_lower:
                    provider_info.update({
                        'provider_type': 'Free',
                        'is_free': True,
                        'provider_name': provider
                    })
                    return provider_info
            
            # Check for business email providers
            for domain, provider in self.business_providers.items():
                if domain in mx_lower:
                    provider_info.update({
                        'provider_type': 'Business',
                        'is_business': True,
                        'provider_name': provider
                    })
                    return provider_info
        
        # Check for common business patterns
        for mx_record in mx_records:
            mx_lower = mx_record.lower()
            
            # Google Workspace patterns
            if any(pattern in mx_lower for pattern in ['aspmx.l.google.com', 'alt1.aspmx.l.google.com', 'alt2.aspmx.l.google.com']):
                provider_info.update({
                    'provider_type': 'Business',
                    'is_business': True,
                    'provider_name': 'Google Workspace'
                })
                return provider_info
            
            # Microsoft 365 patterns
            if any(pattern in mx_lower for pattern in ['outlook.office365.com', 'mail.protection.outlook.com']):
                provider_info.update({
                    'provider_type': 'Business',
                    'is_business': True,
                    'provider_name': 'Microsoft 365'
                })
                return provider_info
        
        return provider_info

