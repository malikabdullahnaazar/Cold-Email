# Email Discovery & Validation API

A scalable FastAPI service for discovering email addresses from domains and validating email addresses with comprehensive checks.

## Features

- **Email Discovery**: Find emails from domains using web scraping, pattern matching, and third-party integrations
- **Email Validation**: Validate emails with syntax, DNS, and SMTP verification
- **Scalable Architecture**: Extensible design for third-party integrations
- **Caching**: Redis and in-memory caching for improved performance
- **Rate Limiting**: API key-based rate limiting
- **Authentication**: API key authentication
- **Comprehensive Logging**: Structured logging with configurable levels

## Quick Start

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Cold-Email
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create environment file:
```bash
cp .env.example .env
```

4. Configure your environment variables in `.env`:
```env
API_KEYS=your-api-key-1,your-api-key-2
RATE_LIMIT_PER_MINUTE=10
CACHE_TTL_SECONDS=3600
REDIS_URL=redis://localhost:6379  # Optional
SMTP_TIMEOUT=10
ENABLE_THIRD_PARTY=false
HUNTER_IO_API_KEY=your-hunter-io-key  # Optional
```

5. Run the application:
```bash
python -m app.main
```

The API will be available at `http://localhost:8000`

## API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## API Endpoints

### 1. Email Discovery

**POST** `/api/v1/discover`

Discover email addresses for a given domain.

**Request:**
```json
{
  "domain": "falconxoft.com",
  "methods": ["scraping", "patterns", "third_party"],
  "detailed": true
}
```

**Response:**
```json
{
  "domain": "falconxoft.com",
  "emails": [
    {
      "email": "info@falconxoft.com",
      "source": "common_pattern",
      "confidence": 0.7,
      "found_at": null
    },
    {
      "email": "contact@falconxoft.com",
      "source": "web_scraping",
      "confidence": 0.9,
      "found_at": "https://falconxoft.com/contact"
    }
  ],
  "total_found": 2,
  "cached": false,
  "methods_used": ["scraping", "patterns"]
}
```

### 2. Email Validation

**POST** `/api/v1/validate`

Validate an email address.

**Request:**
```json
{
  "email": "abc@falconxoft.com",
  "validation_level": "advanced",
  "detailed": true
}
```

**Response:**
```json
{
  "email": "abc@falconxoft.com",
  "valid": true,
  "validation_results": {
    "syntax": {
      "valid": true,
      "message": "Email syntax is valid",
      "details": {
        "normalized_email": "abc@falconxoft.com",
        "local_part": "abc",
        "domain": "falconxoft.com"
      }
    },
    "dns": {
      "valid": true,
      "message": "Domain has valid MX records",
      "details": {
        "mx_records": ["mail.falconxoft.com"],
        "mx_count": 1
      }
    },
    "smtp": {
      "valid": true,
      "message": "Mailbox exists and accepts emails",
      "details": {
        "mx_record": "mail.falconxoft.com",
        "mailbox_exists": true,
        "can_deliver": true
      }
    }
  },
  "risk_score": 0.1,
  "cached": false
}
```

## Authentication

All endpoints require API key authentication. Include your API key in the request header:

```
X-API-Key: your-api-key
```

Or use Authorization header:

```
Authorization: Bearer your-api-key
```

## Discovery Methods

### 1. Web Scraping
- Scrapes the domain's website for email addresses
- Follows internal links to find more emails
- High confidence score (0.9)

### 2. Pattern Matching
- Generates common email patterns (info@, contact@, admin@, etc.)
- Medium confidence score (0.7)
- Always available

### 3. Third-Party Integration
- Integrates with external services like Hunter.io
- Requires API key configuration
- Confidence varies by provider

## Validation Levels

### Basic
- Syntax validation
- DNS/MX record validation

### Advanced
- Syntax validation
- DNS/MX record validation
- SMTP mailbox verification

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_KEYS` | Comma-separated list of API keys | Required |
| `RATE_LIMIT_PER_MINUTE` | Rate limit per API key | 10 |
| `CACHE_TTL_SECONDS` | Cache TTL in seconds | 3600 |
| `REDIS_URL` | Redis connection URL | None (uses in-memory) |
| `SMTP_TIMEOUT` | SMTP validation timeout | 10 |
| `SMTP_MAX_RETRIES` | SMTP validation retries | 3 |
| `ENABLE_THIRD_PARTY` | Enable third-party integrations | false |
| `HUNTER_IO_API_KEY` | Hunter.io API key | None |
| `LOG_LEVEL` | Logging level | INFO |

## Third-Party Integration

### Adding New Providers

1. Create a new provider class in `app/services/email_discovery/third_party/`:

```python
from app.services.email_discovery.base import EmailDiscoveryProvider
from app.models.responses import EmailResult

class MyProvider(EmailDiscoveryProvider):
    async def discover(self, domain: str) -> List[EmailResult]:
        # Implementation
        pass
    
    def is_available(self) -> bool:
        # Check if provider is available
        return True
    
    def get_name(self) -> str:
        return "my_provider"
```

2. Register the provider in the discovery router:

```python
providers["my_provider"] = MyProvider()
```

### Hunter.io Integration

1. Get API key from [Hunter.io](https://hunter.io)
2. Set `ENABLE_THIRD_PARTY=true` in `.env`
3. Set `HUNTER_IO_API_KEY=your-key` in `.env`
4. Use `"third_party"` in discovery methods

## Error Handling

The API returns appropriate HTTP status codes:

- `200`: Success
- `400`: Bad Request (invalid input)
- `401`: Unauthorized (invalid API key)
- `429`: Too Many Requests (rate limit exceeded)
- `500`: Internal Server Error

Error responses include detailed error messages:

```json
{
  "error": "Invalid API key",
  "detail": "API key required. Provide X-API-Key header or Authorization Bearer token.",
  "status_code": 401
}
```

## Performance

- **Caching**: Results are cached to avoid repeated lookups
- **Concurrent Processing**: Discovery methods run concurrently
- **Rate Limiting**: Prevents abuse and ensures fair usage
- **Async Operations**: Non-blocking I/O for better performance

## Monitoring

- Structured logging with configurable levels
- Health check endpoint at `/health`
- Comprehensive error tracking
- Performance metrics in logs

## Development

### Running in Development

```bash
python -m app.main
```

### Running with Uvicorn

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Running with Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## License

This project is licensed under the MIT License.

