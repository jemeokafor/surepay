from fastapi import FastAPI
from starlette.requests import Request
import re
import html

def add_security_middleware(app: FastAPI):
    """
    Add security middleware to the FastAPI app
    """
    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
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
    sanitized = re.sub(r'<[^>]*>', '', text)
    sanitized = html.escape(sanitized)
    return sanitized[:1000]

def validate_email(email: str) -> bool:
    """
    Validate email format
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """
    Validate Nigerian phone number format
    """
    pattern = r'^(\+234|0)[789][01]\d{8}$'
    return re.match(pattern, phone) is not None

def validate_amount(amount: int) -> bool:
    """
    Validate payment amount
    """
    return isinstance(amount, int) and amount > 0 and amount <= 10000000

def validate_currency(currency: str) -> bool:
    """
    Validate currency code
    """
    return currency == "NGN"

def encrypt_sensitive_data(data: str) -> str:
    """
    Encrypt sensitive data using Fernet encryption
    """
    from cryptography.fernet import Fernet
    import os

    key = os.environ.get('ENCRYPTION_KEY')
    if not key:
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
