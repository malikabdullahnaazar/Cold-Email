import asyncio
import socket
import smtplib
import random
import string
from typing import Tuple, Optional, List
from app.models.responses import ValidationResult
from app.config import settings
from app.utils.logger import logger
from app.services.email_validation.disposable_detector import disposable_detector


class SMTPValidator:
    """SMTP mailbox validation"""
    
    def __init__(self, timeout: int = None, max_retries: int = None):
        self.timeout = timeout or settings.smtp_timeout
        self.max_retries = max_retries or settings.smtp_max_retries
    
    async def validate(self, email: str, mx_records: List[str]) -> ValidationResult:
        """Validate if mailbox exists using SMTP"""
        if not mx_records:
            return ValidationResult(
                valid=False,
                message="No MX records available for SMTP validation",
                details={"error_type": "no_mx_records"},
                is_disposable=False
            )
        
        # Check if email is disposable
        is_disposable = await disposable_detector.is_disposable(email)
        
        # Try each MX record
        for mx_record in mx_records:
            try:
                result = await self._check_mailbox_smtp(email, mx_record)
                if result[0]:  # Valid
                    # Check for catch-all
                    is_catch_all = await self._check_catch_all(email, mx_record)
                    
                    return ValidationResult(
                        valid=True,
                        message="Mailbox exists and accepts emails",
                        details={
                            "mx_record": mx_record,
                            "mailbox_exists": result[1],
                            "can_deliver": result[2],
                            "is_catch_all": is_catch_all
                        },
                        is_catch_all=is_catch_all,
                        is_disposable=is_disposable
                    )
            except Exception as e:
                logger.debug(f"SMTP check failed for {mx_record}: {e}")
                continue
        
        return ValidationResult(
            valid=False,
            message="Mailbox does not exist or is not accepting emails",
            details={"error_type": "mailbox_not_found"},
            is_disposable=is_disposable
        )
    
    async def _check_mailbox_smtp(self, email: str, mx_record: str) -> Tuple[bool, bool, bool]:
        """Check mailbox using SMTP"""
        try:
            # Run SMTP check in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                self._smtp_check_sync, 
                email, 
                mx_record
            )
            return result
        except Exception as e:
            logger.debug(f"SMTP check error for {email} via {mx_record}: {e}")
            return False, False, False
    
    def _smtp_check_sync(self, email: str, mx_record: str) -> Tuple[bool, bool, bool]:
        """Synchronous SMTP check"""
        try:
            # Connect to SMTP server
            with smtplib.SMTP(mx_record, 25, timeout=self.timeout) as server:
                server.set_debuglevel(0)
                
                # Get local hostname
                local_hostname = socket.getfqdn()
                
                # Start SMTP conversation
                server.helo(local_hostname)
                
                # Check if server supports VRFY
                if server.has_extn('VRFY'):
                    try:
                        code, message = server.verify(email)
                        if code == 250:
                            return True, True, True
                    except smtplib.SMTPException:
                        pass
                
                # Try MAIL FROM and RCPT TO
                try:
                    server.mail('test@example.com')
                    code, message = server.rcpt(email)
                    
                    if code == 250:
                        return True, True, True
                    elif code in [450, 451, 452, 550, 551, 552, 553]:
                        return False, False, False  # Mailbox doesn't exist
                    else:
                        return False, False, False  # Unknown response
                
                except smtplib.SMTPException as e:
                    if "550" in str(e) or "User unknown" in str(e):
                        return False, False, False  # Mailbox doesn't exist
                    else:
                        return False, False, False  # Other error
        
        except (socket.timeout, socket.gaierror, smtplib.SMTPException) as e:
            logger.debug(f"SMTP connection error: {e}")
            return False, False, False
        
        except Exception as e:
            logger.debug(f"Unexpected SMTP error: {e}")
            return False, False, False
    
    async def _check_catch_all(self, email: str, mx_record: str) -> bool:
        """Check if domain uses catch-all email"""
        try:
            domain = email.split('@')[1]
            
            # Generate a random email address for the same domain
            random_username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
            test_email = f"{random_username}@{domain}"
            
            # Check if the random email is accepted
            result = await self._check_mailbox_smtp(test_email, mx_record)
            
            # If random email is accepted, it's likely a catch-all
            return result[0] and result[1]
            
        except Exception as e:
            logger.debug(f"Catch-all check failed for {email}: {e}")
            return False
