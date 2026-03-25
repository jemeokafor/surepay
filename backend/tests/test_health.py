import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

def test_health_check(client):
    """Test the basic health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data

def test_health_check_supabase(client):
    """Test the Supabase health check endpoint"""
    with patch('app.services.supabase.get_health', new=AsyncMock(return_value="connected")):
        response = client.get("/health/supabase")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

def test_health_check_paystack(client):
    """Test the Paystack health check endpoint"""
    with patch('app.services.paystack.get_health', new=AsyncMock(return_value="connected")):
        response = client.get("/health/paystack")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

def test_health_check_all(client):
    """Test the full health check endpoint"""
    with patch('app.services.supabase.get_health', new=AsyncMock(return_value="connected")), \
         patch('app.services.paystack.get_health', new=AsyncMock(return_value="connected")):
        response = client.get("/health/all")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data