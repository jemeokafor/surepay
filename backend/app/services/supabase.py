from supabase import create_client, Client
from app.core.config import settings
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class SupabaseService:
    def __init__(self):
        self.client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY
        )
    
    async def get_transaction(self, transaction_id: str) -> Optional[Dict[Any, Any]]:
        """
        Get transaction by ID
        """
        try:
            response = self.client.table('transactions').select('*').eq('id', transaction_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error getting transaction {transaction_id}: {str(e)}")
            return None
    
    async def create_transaction(self, transaction_id: str, amount: int, currency: str, vendor_id: str, product_id: str = None, metadata: dict = None) -> Dict[Any, Any]:
        """
        Create a new transaction
        """
        transaction_data = {
            'id': transaction_id,
            'amount': amount,
            'currency': currency,
            'vendor_id': vendor_id,
            'product_id': product_id,
            'status': 'PENDING_PAYMENT',
            'metadata': metadata or {}
        }
        
        response = self.client.table('transactions').insert(transaction_data).execute()
        return response.data[0]
    
    async def update_transaction_status(self, transaction_id: str, status: str, amount: int = None) -> bool:
        """
        Update transaction status
        """
        try:
            update_data = {'status': status}
            if amount:
                update_data['amount'] = amount
                
            self.client.table('transactions').update(update_data).eq('id', transaction_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error updating transaction {transaction_id} status: {str(e)}")
            return False
    
    async def update_transaction_paystack_details(self, transaction_id: str, authorization_url: str, access_code: str) -> bool:
        """
        Update transaction with Paystack details
        """
        try:
            update_data = {
                'paystack_authorization_url': authorization_url,
                'paystack_access_code': access_code
            }
            
            self.client.table('transactions').update(update_data).eq('id', transaction_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error updating transaction {transaction_id} Paystack details: {str(e)}")
            return False
    
    async def get_payout_by_transaction(self, transaction_id: str) -> Optional[Dict[Any, Any]]:
        """
        Get payout by transaction ID
        """
        try:
            response = self.client.table('payouts').select('*').eq('transaction_id', transaction_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error getting payout for transaction {transaction_id}: {str(e)}")
            return None
    
    async def create_payout(self, transaction_id: str, vendor_id: str, amount: int, transfer_id: str, idempotency_key: str, status: str) -> Dict[Any, Any]:
        """
        Create a new payout record
        """
        payout_data = {
            'transaction_id': transaction_id,
            'vendor_id': vendor_id,
            'amount': amount,
            'transfer_id': transfer_id,
            'idempotency_key': idempotency_key,
            'status': status
        }
        
        response = self.client.table('payouts').insert(payout_data).execute()
        return response.data[0]
    
    async def update_payout_status(self, transaction_id: str, status: str, transfer_id: str = None, failure_reason: str = None) -> bool:
        """
        Update payout status
        """
        try:
            update_data = {'status': status}
            if transfer_id:
                update_data['transfer_id'] = transfer_id
            if failure_reason:
                update_data['failure_reason'] = failure_reason
                
            self.client.table('payouts').update(update_data).eq('transaction_id', transaction_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error updating payout for transaction {transaction_id} status: {str(e)}")
            return False
    
    async def update_payout_retry(self, payout_id: str, transfer_id: str, idempotency_key: str, status: str) -> bool:
        """
        Update payout for retry
        """
        try:
            update_data = {
                'transfer_id': transfer_id,
                'idempotency_key': idempotency_key,
                'status': status,
                'retry_count': self.client.table('payouts').select('retry_count').eq('id', payout_id).execute().data[0].get('retry_count', 0) + 1
            }
            
            self.client.table('payouts').update(update_data).eq('id', payout_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error updating payout {payout_id} for retry: {str(e)}")
            return False
    
    async def get_vendor(self, vendor_id: str) -> Optional[Dict[Any, Any]]:
        """
        Get vendor by ID
        """
        try:
            response = self.client.table('vendors').select('*').eq('id', vendor_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error getting vendor {vendor_id}: {str(e)}")
            return None
    
    async def update_vendor_paystack_recipient_id(self, vendor_id: str, recipient_id: str) -> bool:
        """
        Update vendor with Paystack recipient ID
        """
        try:
            self.client.table('vendors').update({'paystack_recipient_id': recipient_id}).eq('id', vendor_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error updating vendor {vendor_id} Paystack recipient ID: {str(e)}")
            return False
    
    async def get_health(self) -> str:
        """
        Check Supabase connection health
        """
        try:
            self.client.table('transactions').select('id').limit(1).execute()
            return "connected"
        except Exception as e:
            return f"disconnected: {str(e)}"

# Create singleton instance
supabase_service = SupabaseService()

# Export functions for easier import
get_transaction = supabase_service.get_transaction
create_transaction = supabase_service.create_transaction
update_transaction_status = supabase_service.update_transaction_status
update_transaction_paystack_details = supabase_service.update_transaction_paystack_details
get_payout_by_transaction = supabase_service.get_payout_by_transaction
create_payout = supabase_service.create_payout
update_payout_status = supabase_service.update_payout_status
update_payout_retry = supabase_service.update_payout_retry
get_vendor = supabase_service.get_vendor
update_vendor_paystack_recipient_id = supabase_service.update_vendor_paystack_recipient_id
get_health = supabase_service.get_health