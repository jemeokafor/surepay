from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import json

class DataEncryption:
    """
    Data encryption module for GDPR compliance and sensitive data protection
    """
    
    def __init__(self, password: str = None):
        """
        Initialize encryption with optional password
        In production, use a proper key management system
        """
        self.password = password or os.environ.get('ENCRYPTION_PASSWORD', 'surepay-default-password')
        self.key = self._derive_key()
        self.cipher = Fernet(self.key)
    
    def _derive_key(self) -> bytes:
        """
        Derive encryption key from password
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'surepay-salt-2026',  # In production, use random salt
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.password.encode()))
        return key
    
    def encrypt_data(self, data: str) -> str:
        """
        Encrypt sensitive data
        """
        if not isinstance(data, str):
            data = str(data)
        
        encrypted_data = self.cipher.encrypt(data.encode())
        return encrypted_data.decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive data
        """
        decrypted_data = self.cipher.decrypt(encrypted_data.encode())
        return decrypted_data.decode()
    
    def encrypt_user_data(self, user_data: dict) -> dict:
        """
        Encrypt user personal data
        """
        encrypted_data = {}
        
        # Fields that should be encrypted
        sensitive_fields = [
            'phone_number',
            'bank_account_number',
            'id_number',
            'address',
            'whatsapp_number'
        ]
        
        for key, value in user_data.items():
            if key in sensitive_fields and value:
                encrypted_data[key] = self.encrypt_data(str(value))
            else:
                encrypted_data[key] = value
        
        return encrypted_data
    
    def decrypt_user_data(self, encrypted_user_data: dict) -> dict:
        """
        Decrypt user personal data
        """
        decrypted_data = {}
        
        # Fields that were encrypted
        sensitive_fields = [
            'phone_number',
            'bank_account_number',
            'id_number',
            'address',
            'whatsapp_number'
        ]
        
        for key, value in encrypted_user_data.items():
            if key in sensitive_fields and value:
                try:
                    decrypted_data[key] = self.decrypt_data(str(value))
                except Exception:
                    # If decryption fails, keep encrypted value
                    decrypted_data[key] = value
            else:
                decrypted_data[key] = value
        
        return decrypted_data
    
    def hash_sensitive_field(self, value: str) -> str:
        """
        Hash sensitive fields for comparison without decryption
        """
        import hashlib
        return hashlib.sha256(value.encode()).hexdigest()
    
    def generate_encryption_key(self) -> str:
        """
        Generate a new encryption key
        """
        return Fernet.generate_key().decode()

# Global encryption instance
encryption_service = DataEncryption()

def encrypt_sensitive_data(data: str) -> str:
    """
    Encrypt sensitive data using the global encryption service
    """
    return encryption_service.encrypt_data(data)

def decrypt_sensitive_data(encrypted_data: str) -> str:
    """
    Decrypt sensitive data using the global encryption service
    """
    return encryption_service.decrypt_data(encrypted_data)

def encrypt_user_personal_data(user_data: dict) -> dict:
    """
    Encrypt user personal data
    """
    return encryption_service.encrypt_user_data(user_data)

def decrypt_user_personal_data(encrypted_user_data: dict) -> dict:
    """
    Decrypt user personal data
    """
    return encryption_service.decrypt_user_data(encrypted_user_data)

def hash_for_privacy(value: str) -> str:
    """
    Hash sensitive data for privacy-preserving comparisons
    """
    return encryption_service.hash_sensitive_field(value)