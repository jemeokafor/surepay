from fastapi import APIRouter, HTTPException
from app.services import paystack, supabase
from app.core.config import settings
import uuid
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/create")
async def create_payout(payout_data: dict):
    """
    Create a new payout transfer
    """
    try:
        transaction_id = payout_data['transaction_id']
        vendor_id = payout_data['vendor_id']
        amount = payout_data['amount']
        
        # Get transaction to verify it's in RELEASED state
        transaction = await supabase.get_transaction(transaction_id)
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        if transaction['status'] != 'RELEASED':
            raise HTTPException(status_code=400, detail="Transaction not in RELEASED state")
        
        # Check if payout already exists
        existing_payout = await supabase.get_payout_by_transaction(transaction_id)
        if existing_payout:
            raise HTTPException(status_code=400, detail="Payout already created for this transaction")
        
        # Get vendor bank details
        vendor = await supabase.get_vendor(vendor_id)
        if not vendor or not vendor.get('bank_account'):
            raise HTTPException(status_code=400, detail="Vendor bank account not found")
        
        # Create transfer recipient if needed
        recipient_id = vendor.get('paystack_recipient_id')
        if not recipient_id:
            recipient = await paystack.create_transfer_recipient(
                name=vendor['name'],
                account_number=vendor['bank_account']['account_number'],
                bank_code=vendor['bank_account']['bank_code']
            )
            recipient_id = recipient['data']['recipient_code']
            
            # Save recipient ID to vendor
            await supabase.update_vendor_paystack_recipient_id(vendor_id, recipient_id)
        
        # Generate idempotency key to prevent duplicate transfers
        idempotency_key = f"payout_{transaction_id}_{uuid.uuid4().hex}"
        
        # Create transfer
        transfer = await paystack.initiate_transfer(
            amount=amount,
            recipient=recipient_id,
            reference=transaction_id,
            idempotency_key=idempotency_key
        )
        
        # Create payout record
        payout = await supabase.create_payout(
            transaction_id=transaction_id,
            vendor_id=vendor_id,
            amount=amount,
            transfer_id=transfer['data']['id'],
            idempotency_key=idempotency_key,
            status='PENDING'
        )
        
        return {
            "status": "success",
            "payout_id": payout['id'],
            "transfer_id": transfer['data']['id'],
            "transfer_status": transfer['data']['status']
        }
        
    except Exception as e:
        logger.error(f"Payout creation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/retry/{transaction_id}")
async def retry_payout(transaction_id: str):
    """
    Retry a failed payout
    """
    try:
        # Get payout details
        payout = await supabase.get_payout_by_transaction(transaction_id)
        if not payout:
            raise HTTPException(status_code=404, detail="Payout not found")
        
        if payout['status'] != 'FAILED':
            raise HTTPException(status_code=400, detail="Payout is not in FAILED state")
        
        # Get transaction and vendor details
        transaction = await supabase.get_transaction(transaction_id)
        vendor = await supabase.get_vendor(transaction['vendor_id'])
        
        # Generate new idempotency key
        idempotency_key = f"payout_{transaction_id}_{uuid.uuid4().hex}"
        
        # Retry transfer
        transfer = await paystack.initiate_transfer(
            amount=payout['amount'],
            recipient=vendor['paystack_recipient_id'],
            reference=transaction_id,
            idempotency_key=idempotency_key
        )
        
        # Update payout record
        await supabase.update_payout_retry(
            payout['id'],
            transfer['data']['id'],
            idempotency_key,
            'PENDING'
        )
        
        return {
            "status": "success",
            "transfer_id": transfer['data']['id'],
            "transfer_status": transfer['data']['status']
        }
        
    except Exception as e:
        logger.error(f"Payout retry failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))