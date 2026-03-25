from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse
import re
import html

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

def add_security_middleware(app: FastAPI):
    """
    Add security middleware to the FastAPI app
    """
    # Add rate limiter to app
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # Add security headers middleware
    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent XSS and other injection attacks
    """
    if not isinstance(text, str):
        return str(text)
    
    # Remove HTML tags
    sanitized = re.sub(r'<[^>]*>', '', text)
    
    # HTML escape dangerous characters
    sanitized = html.escape(sanitized)
    
    # Limit length to prevent DoS
    return sanitized[:1000]

def validate_email(email: str) -> bool:
    """
    Validate email format
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """
    Validate Nigerian phone number format
    """
    import re
    pattern = r'^(\+234|0)[789][01]\d{8}$'
    return re.match(pattern, phone) is not None

def validate_amount(amount: int) -> bool:
    """
    Validate payment amount
    """
    # Amount should be positive and within reasonable limits
    return isinstance(amount, int) and amount > 0 and amount <= 10000000  # Max 100,000 NGN

def validate_currency(currency: str) -> bool:
    """
    Validate currency code
    """
    return currency == "NGN"  # Only Nigerian Naira supported for now

def encrypt_sensitive_data(data: str) -> str:
    """
    Encrypt sensitive data using Fernet encryption
    Note: In production, use a proper key management system
    """
    from cryptography.fernet import Fernet
    import os
    
    # Generate or get encryption key
    key = os.environ.get('ENCRYPTION_KEY')
    if not key:
        # In production, this should be securely stored and managed
        key = Fernet.generate_key()
        os.environ['ENCRYPTION_KEY'] = key.decode()
    
    f = Fernet(key.encode())
    return f.encrypt(data.encode()).decode()

def decrypt_sensitive_data(encrypted_data: str) -> str:
    """
    Decrypt sensitive data
    """
    from cryptography.fernet import Fernet
    import os
    
    key = os.environ.get('ENCRYPTION_KEY')
    if not key:
        raise ValueError("Encryption key not found")
    
    f = Fernet(key.encode())
    return f.decrypt(encrypted_data.encode()).decode()

# Rate limiting decorators for different endpoints
def rate_limit_payment_initialization():
    """Rate limit for payment initialization - 10 per minute per IP"""
    return limiter.limit("10/minute")

def rate_limit_payout_creation():
    """Rate limit for payout creation - 5 per minute per IP"""
    return limiter.limit("5/minute")

def rate_limit_webhook():
    """Rate limit for webhooks - 100 per minute per IP"""
    return limiter.limit("100/minute")

def rate_limit_generic():
    """Generic rate limit - 60 per minute per IP"""
    return limiter.limit("60/minute")