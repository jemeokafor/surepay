import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx
from httpx import Response
from app.services.paystack import PaystackAPI

@pytest.fixture
def paystack_api():
    """Create a PaystackAPI instance with mocked client"""
    with patch('app.services.paystack.httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        api = PaystackAPI()
        api.client = mock_client
        return api

@pytest.mark.asyncio
async def test_initialize_transaction_success(paystack_api):
    """Test successful transaction initialization"""
    # Mock response
    mock_response = Mock()
    mock_response.json.return_value = {
        "status": True,
        "data": {
            "authorization_url": "https://paystack.com/pay/test",
            "access_code": "test_access_code"
        }
    }
    mock_response.raise_for_status.return_value = None
    paystack_api.client.post.return_value = mock_response
    
    result = await paystack_api.initialize_transaction(
        amount=10000,
        email="test@example.com",
        reference="test_ref_123"
    )
    
    assert result["status"] is True
    assert "authorization_url" in result["data"]

@pytest.mark.asyncio
async def test_verify_transaction_success(paystack_api):
    """Test successful transaction verification"""
    # Mock response
    mock_response = Mock()
    mock_response.json.return_value = {
        "status": True,
        "data": {
            "status": "success"
        }
    }
    mock_response.raise_for_status.return_value = None
    paystack_api.client.get.return_value = mock_response
    
    result = await paystack_api.verify_transaction("test_ref_123")
    
    assert result["status"] is True
    assert result["data"]["status"] == "success"

@pytest.mark.asyncio
async def test_create_transfer_recipient_success(paystack_api):
    """Test successful transfer recipient creation"""
    # Mock response
    mock_response = Mock()
    mock_response.json.return_value = {
        "status": True,
        "data": {
            "recipient_code": "recipient_123"
        }
    }
    mock_response.raise_for_status.return_value = None
    paystack_api.client.post.return_value = mock_response
    
    result = await paystack_api.create_transfer_recipient(
        name="Test Vendor",
        account_number="1234567890",
        bank_code="058"
    )
    
    assert result["status"] is True
    assert "recipient_code" in result["data"]

@pytest.mark.asyncio
async def test_initiate_transfer_success(paystack_api):
    """Test successful transfer initiation"""
    # Mock response
    mock_response = Mock()
    mock_response.json.return_value = {
        "status": True,
        "data": {
            "id": "transfer_123",
            "status": "pending"
        }
    }
    mock_response.raise_for_status.return_value = None
    paystack_api.client.post.return_value = mock_response
    
    result = await paystack_api.initiate_transfer(
        amount=9500,
        recipient="recipient_123",
        reference="test_ref_123"
    )
    
    assert result["status"] is True
    assert "id" in result["data"]

@pytest.mark.asyncio
async def test_get_health_success(paystack_api):
    """Test successful health check"""
    # Mock response
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    paystack_api.client.get.return_value = mock_response
    
    result = await paystack_api.get_health()
    
    assert result == "connected"

@pytest.mark.asyncio
async def test_get_health_failure(paystack_api):
    """Test failed health check"""
    # Mock failed response
    paystack_api.client.get.side_effect = Exception("API unavailable")
    
    result = await paystack_api.get_health()
    
    assert "disconnected" in result