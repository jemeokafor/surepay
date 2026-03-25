from fastapi import APIRouter, HTTPException, Request
from app.services import paystack, supabase
from app.core.config import settings
from app.core.security_middleware import (
    rate_limit_payout_creation, 
    sanitize_input, 
    validate_amount
)
from app.core.monitoring import business_analytics, performance_monitor
import uuid
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/create")
async def create_payout(request: Request, payout_data: dict):
    """
    Create a new payout transfer
    Rate limited to 5 requests per minute per IP
    """
    # Start performance timer
    timer_id = performance_monitor.start_timer("payout_creation")
    
    try:
        # Validate and sanitize inputs
        transaction_id = payout_data.get('transaction_id')
        vendor_id = payout_data.get('vendor_id')
        amount = payout_data.get('amount')
        
        # Validate required fields
        if not transaction_id or not vendor_id or not amount:
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Validate amount
        if not validate_amount(amount):
            raise HTTPException(status_code=400, detail="Invalid amount")
        
        # Sanitize inputs
        sanitized_transaction_id = sanitize_input(transaction_id)
        sanitized_vendor_id = sanitize_input(vendor_id)
        
        # Get transaction to verify it's in RELEASED state
        transaction = await supabase.get_transaction(sanitized_transaction_id)
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        if transaction['status'] != 'RELEASED':
            raise HTTPException(status_code=400, detail="Transaction not in RELEASED state")
        
        # Check if payout already exists
        existing_payout = await supabase.get_payout_by_transaction(sanitized_transaction_id)
        if existing_payout:
            raise HTTPException(status_code=400, detail="Payout already created for this transaction")
        
        # Get vendor bank details
        vendor = await supabase.get_vendor(sanitized_vendor_id)
        if not vendor or not vendor.get('bank_account'):
            raise HTTPException(status_code=400, detail="Vendor bank account not found")
        
        # Create transfer recipient if needed
        recipient_id = vendor.get('paystack_recipient_id')
        if not recipient_id:
            # Sanitize bank details
            account_number = sanitize_input(vendor['bank_account']['account_number'])
            bank_code = sanitize_input(vendor['bank_account']['bank_code'])
            name = sanitize_input(vendor.get('name', 'Vendor'))
            
            recipient = await paystack.create_transfer_recipient(
                name=name,
                account_number=account_number,
                bank_code=bank_code
            )
            recipient_id = recipient['data']['recipient_code']
            
            # Save recipient ID to vendor
            await supabase.update_vendor_paystack_recipient_id(sanitized_vendor_id, recipient_id)
        
        # Generate idempotency key to prevent duplicate transfers
        idempotency_key = f"payout_{sanitized_transaction_id}_{uuid.uuid4().hex}"
        
        # Create transfer
        transfer = await paystack.initiate_transfer(
            amount=amount,
            recipient=recipient_id,
            reference=sanitized_transaction_id,
            idempotency_key=idempotency_key
        )
        
        # Create payout record
        payout = await supabase.create_payout(
            transaction_id=sanitized_transaction_id,
            vendor_id=sanitized_vendor_id,
            amount=amount,
            transfer_id=transfer['data']['id'],
            idempotency_key=idempotency_key,
            status='PENDING'
        )
        
        # End performance timer
        duration = performance_monitor.end_timer(timer_id)
        performance_monitor.log_metric("payout_creation_duration", duration)
        
        return {
            "status": "success",
            "payout_id": payout['id'],
            "transfer_id": transfer['data']['id'],
            "transfer_status": transfer['data']['status']
        }
        
    except Exception as e:
        logger.error(f"Payout creation failed: {str(e)}")
        # End performance timer on error
        performance_monitor.end_timer(timer_id)
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/retry/{transaction_id}")
async def retry_payout(transaction_id: str):
    """
    Retry a failed payout
    """
    # Sanitize transaction_id
    sanitized_transaction_id = sanitize_input(transaction_id)
    
    # Start performance timer
    timer_id = performance_monitor.start_timer("payout_retry")
    
    try:
        # Get payout details
        payout = await supabase.get_payout_by_transaction(sanitized_transaction_id)
        if not payout:
            raise HTTPException(status_code=404, detail="Payout not found")
        
        if payout['status'] != 'FAILED':
            raise HTTPException(status_code=400, detail="Payout is not in FAILED state")
        
        # Get transaction and vendor details
        transaction = await supabase.get_transaction(sanitized_transaction_id)
        vendor = await supabase.get_vendor(transaction['vendor_id'])
        
        # Generate new idempotency key
        idempotency_key = f"payout_{sanitized_transaction_id}_{uuid.uuid4().hex}"
        
        # Retry transfer
        transfer = await paystack.initiate_transfer(
            amount=payout['amount'],
            recipient=vendor['paystack_recipient_id'],
            reference=sanitized_transaction_id,
            idempotency_key=idempotency_key
        )
        
        # Update payout record
        await supabase.update_payout_retry(
            payout['id'],
            transfer['data']['id'],
            idempotency_key,
            'PENDING'
        )
        
        # Track successful payout retry
        business_analytics.track_payout(amount=payout['amount'])
        
        # End performance timer
        duration = performance_monitor.end_timer(timer_id)
        performance_monitor.log_metric("payout_retry_duration", duration)
        
        return {
            "status": "success",
            "transfer_id": transfer['data']['id'],
            "transfer_status": transfer['data']['status']
        }
        
    except Exception as e:
        logger.error(f"Payout retry failed: {str(e)}")
        # End performance timer on error
        performance_monitor.end_timer(timer_id)
        raise HTTPException(status_code=400, detail=str(e))