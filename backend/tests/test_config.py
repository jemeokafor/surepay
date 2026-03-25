import pytest
import os
from unittest.mock import patch
from app.core.config import Settings

def test_settings_defaults():
    """Test that Settings loads with defaults"""
    # Test with minimal environment
    with patch.dict(os.environ, {}, clear=True):
        settings = Settings()
        assert settings.FRONTEND_URL == "http://localhost:3000"
        assert settings.API_URL == "http://localhost:8000"

def test_settings_from_env():
    """Test that Settings loads from environment variables"""
    test_env = {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "test-key",
        "PAYSTACK_SECRET_KEY": "sk_test_123",
        "PAYSTACK_WEBHOOK_SECRET": "whsec_123",
        "FRONTEND_URL": "https://test.example.com"
    }
    
    with patch.dict(os.environ, test_env, clear=True):
        settings = Settings()
        assert settings.SUPABASE_URL == "https://test.supabase.co"
        assert settings.SUPABASE_SERVICE_ROLE_KEY == "test-key"
        assert settings.PAYSTACK_SECRET_KEY == "sk_test_123"
        assert settings.PAYSTACK_WEBHOOK_SECRET == "whsec_123"
        assert settings.FRONTEND_URL == "https://test.example.com"