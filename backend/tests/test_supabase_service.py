import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.supabase import SupabaseService

@pytest.fixture
def supabase_service():
    """Create a SupabaseService instance with mocked client"""
    with patch('app.services.supabase.create_client') as mock_create:
        mock_client = Mock()
        mock_create.return_value = mock_client
        service = SupabaseService()
        service.client = mock_client
        return service

@pytest.mark.asyncio
async def test_get_transaction_success(supabase_service):
    """Test successful transaction retrieval"""
    # Mock response
    mock_response = Mock()
    mock_response.data = [{"id": "txn_123", "amount": 10000}]
    supabase_service.client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
    
    result = await supabase_service.get_transaction("txn_123")
    
    assert result is not None
    assert result["id"] == "txn_123"
    assert result["amount"] == 10000

@pytest.mark.asyncio
async def test_get_transaction_not_found(supabase_service):
    """Test transaction retrieval when not found"""
    # Mock response with empty data
    mock_response = Mock()
    mock_response.data = []
    supabase_service.client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
    
    result = await supabase_service.get_transaction("non_existent")
    
    assert result is None

@pytest.mark.asyncio
async def test_create_transaction(supabase_service):
    """Test transaction creation"""
    # Mock response
    mock_response = Mock()
    mock_response.data = [{"id": "txn_123", "status": "PENDING_PAYMENT"}]
    supabase_service.client.table.return_value.insert.return_value.execute.return_value = mock_response
    
    result = await supabase_service.create_transaction(
        transaction_id="txn_123",
        amount=10000,
        currency="NGN",
        vendor_id="vendor_123"
    )
    
    assert result is not None
    assert result["id"] == "txn_123"

@pytest.mark.asyncio
async def test_update_transaction_status(supabase_service):
    """Test transaction status update"""
    # Mock the update operation
    supabase_service.client.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
    
    result = await supabase_service.update_transaction_status("txn_123", "FUNDS_LOCKED")
    
    assert result is True
    supabase_service.client.table.return_value.update.assert_called_once()

@pytest.mark.asyncio
async def test_get_health_success(supabase_service):
    """Test health check success"""
    # Mock successful health check
    supabase_service.client.table.return_value.select.return_value.limit.return_value.execute.return_value = Mock()
    
    result = await supabase_service.get_health()
    
    assert result == "connected"

@pytest.mark.asyncio
async def test_get_health_failure(supabase_service):
    """Test health check failure"""
    # Mock failed health check
    supabase_service.client.table.return_value.select.return_value.limit.return_value.execute.side_effect = Exception("Connection failed")
    
    result = await supabase_service.get_health()
    
    assert "disconnected" in result