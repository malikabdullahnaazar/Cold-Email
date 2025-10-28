from typing import List
from app.services.email_discovery.base import EmailDiscoveryProvider
from app.models.responses import EmailResult


class PatternMatchingProvider(EmailDiscoveryProvider):
    """Email discovery through common email patterns"""
    
    def __init__(self):
        # Common patterns with confidence scores
        self.common_patterns = {
            "info": 0.6,
            "contact": 0.7,
            "admin": 0.6,
            "support": 0.7,
            "sales": 0.7,
            "marketing": 0.6,
            "hello": 0.5,
            "help": 0.6,
            "service": 0.6,
            "team": 0.6,
            "office": 0.5,
            "general": 0.5,
            "inquiries": 0.6,
            "business": 0.5,
            "careers": 0.6,
            "jobs": 0.6,
            "hr": 0.6,
            "legal": 0.6,
            "billing": 0.6,
            "accounts": 0.6,
            "finance": 0.6,
            "tech": 0.5,
            "technical": 0.5,
            "webmaster": 0.6,
            "postmaster": 0.6,
            "abuse": 0.6,
            "security": 0.6,
            "privacy": 0.6
        }
        
        # Department patterns with higher confidence
        self.department_patterns = {
            "team": 0.7,
            "press": 0.7,
            "media": 0.7,
            "partnerships": 0.7,
            "partners": 0.7,
            "investors": 0.7,
            "investor": 0.7,
            "press@": 0.8,
            "media@": 0.8,
            "partnerships@": 0.8,
            "investors@": 0.8
        }
        
        # Name-based patterns (will be populated with common names)
        self.name_patterns = [
            "john", "jane", "mike", "sarah", "david", "lisa", "chris", "jennifer",
            "robert", "emily", "michael", "jessica", "william", "ashley", "james",
            "amanda", "richard", "samantha", "charles", "stephanie", "thomas",
            "nicole", "christopher", "elizabeth", "daniel", "helen", "matthew",
            "deborah", "anthony", "dorothy", "mark", "linda", "donald", "patricia",
            "steven", "susan", "paul", "barbara", "andrew", "jessica", "joshua",
            "sarah", "kenneth", "karen", "kevin", "nancy", "brian", "betty",
            "george", "helen", "timothy", "sandra", "ronald", "donna", "jason",
            "carol", "edward", "ruth", "jeffrey", "sharon", "ryan", "michelle",
            "jacob", "laura", "gary", "sarah", "nicholas", "kimberly", "eric",
            "deborah", "jonathan", "dorothy", "stephen", "lisa", "larry", "nancy",
            "justin", "karen", "scott", "betty", "brandon", "helen", "benjamin",
            "sandra", "samuel", "donna", "gregory", "carol", "alexander", "ruth",
            "patrick", "sharon", "jack", "michelle", "dennis", "laura", "jerry",
            "sarah", "tyler", "kimberly", "aaron", "deborah", "jose", "dorothy",
            "henry", "lisa", "adam", "nancy", "douglas", "karen", "nathan", "betty",
            "peter", "helen", "zachary", "sandra", "kyle", "donna", "noah", "carol",
            "alan", "ruth", "ethan", "sharon", "jeremy", "michelle", "stephen", "laura"
        ]
    
    async def discover(self, domain: str) -> List[EmailResult]:
        """Generate email patterns for the domain"""
        emails = []
        
        # Add common patterns
        for pattern, confidence in self.common_patterns.items():
            email = f"{pattern}@{domain.lower()}"
            emails.append(EmailResult(
                email=email,
                source="common_pattern",
                confidence=confidence,
                found_at=None
            ))
        
        # Add department patterns
        for pattern, confidence in self.department_patterns.items():
            if pattern.endswith('@'):
                email = f"{pattern}{domain.lower()}"
            else:
                email = f"{pattern}@{domain.lower()}"
            emails.append(EmailResult(
                email=email,
                source="department_pattern",
                confidence=confidence,
                found_at=None
            ))
        
        # Add name-based patterns (limited to avoid too many results)
        for name in self.name_patterns[:20]:  # Limit to first 20 names
            # First name only
            email = f"{name}@{domain.lower()}"
            emails.append(EmailResult(
                email=email,
                source="name_pattern",
                confidence=0.4,  # Lower confidence for name-based
                found_at=None
            ))
            
            # First name + last name patterns (using common last names)
            common_last_names = ["smith", "johnson", "williams", "brown", "jones", "garcia", "miller", "davis"]
            for last_name in common_last_names[:5]:  # Limit to 5 last names
                # first.last@domain
                email = f"{name}.{last_name}@{domain.lower()}"
                emails.append(EmailResult(
                    email=email,
                    source="name_pattern",
                    confidence=0.3,
                    found_at=None
                ))
                
                # firstlast@domain
                email = f"{name}{last_name}@{domain.lower()}"
                emails.append(EmailResult(
                    email=email,
                    source="name_pattern",
                    confidence=0.3,
                    found_at=None
                ))
                
                # f.last@domain
                email = f"{name[0]}.{last_name}@{domain.lower()}"
                emails.append(EmailResult(
                    email=email,
                    source="name_pattern",
                    confidence=0.3,
                    found_at=None
                ))
        
        return emails
    
    def is_available(self) -> bool:
        return True
    
    def get_name(self) -> str:
        return "pattern_matching"

