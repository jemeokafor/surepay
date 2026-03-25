import httpx
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class PaystackAPI:
    def __init__(self):
        self.base_url = "https://api.paystack.co"
        self.headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        # Only create client if we have a valid API key
        self.client = None
        if settings.PAYSTACK_SECRET_KEY:
            self.client = httpx.AsyncClient(base_url=self.base_url, headers=self.headers)
    
    async def _ensure_client(self):
        """Ensure client is initialized"""
        if not self.client and settings.PAYSTACK_SECRET_KEY:
            self.client = httpx.AsyncClient(base_url=self.base_url, headers=self.headers)
        return self.client is not None
    
    async def initialize_transaction(self, amount: int, email: str, reference: str, metadata: dict = None):
        """
        Initialize a new Paystack transaction
        """
        if not await self._ensure_client():
            raise Exception("Paystack client not initialized")
            
        payload = {
            "amount": amount,
            "email": email,
            "reference": reference,
            "callback_url": f"{settings.FRONTEND_URL}/checkout/{reference}/success",
            "metadata": metadata or {}
        }
        
        response = await self.client.post("/transaction/initialize", json=payload)
        response.raise_for_status()
        return response.json()
    
    async def verify_transaction(self, reference: str):
        """
        Verify a Paystack transaction
        """
        if not await self._ensure_client():
            raise Exception("Paystack client not initialized")
            
        response = await self.client.get(f"/transaction/verify/{reference}")
        response.raise_for_status()
        return response.json()
    
    async def create_transfer_recipient(self, name: str, account_number: str, bank_code: str):
        """
        Create a transfer recipient
        """
        if not await self._ensure_client():
            raise Exception("Paystack client not initialized")
            
        payload = {
            "type": "nuban",
            "name": name,
            "account_number": account_number,
            "bank_code": bank_code,
            "currency": "NGN"
        }
        
        response = await self.client.post("/transferrecipient", json=payload)
        response.raise_for_status()
        return response.json()
    
    async def initiate_transfer(self, amount: int, recipient: str, reference: str, idempotency_key: str = None):
        """
        Initiate a transfer
        """
        if not await self._ensure_client():
            raise Exception("Paystack client not initialized")
            
        headers = dict(self.headers)
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
            
        payload = {
            "source": "balance",
            "amount": amount,
            "recipient": recipient,
            "reference": reference
        }
        
        response = await self.client.post("/transfer", json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    
    async def get_transfer(self, transfer_id: str):
        """
        Get transfer details
        """
        if not await self._ensure_client():
            raise Exception("Paystack client not initialized")
            
        response = await self.client.get(f"/transfer/{transfer_id}")
        response.raise_for_status()
        return response.json()
    
    async def get_health(self):
        """
        Check Paystack API health
        """
        if not await self._ensure_client():
            return "disconnected: client not initialized"
            
        try:
            response = await self.client.get("/balance")
            response.raise_for_status()
            return "connected"
        except Exception as e:
            return f"disconnected: {str(e)}"

# Create singleton instance
paystack_api = PaystackAPI()

# Export functions for easier import
initialize_transaction = paystack_api.initialize_transaction
verify_transaction = paystack_api.verify_transaction
create_transfer_recipient = paystack_api.create_transfer_recipient
initiate_transfer = paystack_api.initiate_transfer
get_transfer = paystack_api.get_transfer
get_health = paystack_api.get_health