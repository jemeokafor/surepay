from fastapi import APIRouter, HTTPException, Header, Request, Depends
from app.core.security import verify_paystack_signature, get_raw_body
from app.core.config import settings
from app.services import paystack, supabase
import json
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/paystack")
async def handle_paystack_webhook(
    request: Request,
    payload: bytes = Depends(get_raw_body),
    signature: str = Header(None, alias="x-paystack-signature")
):
    """
    Handle Paystack webhook events
    """
    # Verify signature
    if not verify_paystack_signature(payload, signature):
        logger.warning("Invalid Paystack webhook signature")
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Parse payload
    try:
        event_data = json.loads(payload.decode('utf-8'))
        event_type = event_data.get('event')
        data = event_data.get('data', {})
    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook payload")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    logger.info(f"Received Paystack webhook event: {event_type}")
    
    # Handle different event types
    if event_type == 'charge.success':
        await handle_charge_success(data)
    elif event_type == 'transfer.success':
        await handle_transfer_success(data)
    elif event_type == 'transfer.failed':
        await handle_transfer_failed(data)
    else:
        logger.info(f"Unhandled Paystack event: {event_type}")
    
    return {"status": "success"}

async def handle_charge_success(data: dict):
    """
    Handle successful charge event - funds locked
    """
    transaction_id = data.get('reference')
    amount = data.get('amount')
    
    # Update transaction status to FUNDS_LOCKED
    await supabase.update_transaction_status(
        transaction_id, 
        'FUNDS_LOCKED', 
        amount=amount
    )
    
    logger.info(f"Transaction {transaction_id} updated to FUNDS_LOCKED")

async def handle_transfer_success(data: dict):
    """
    Handle successful transfer event - payout completed
    """
    transfer_id = data.get('id')
    transaction_id = data.get('reference')
    
    # Update payout status to SUCCESS
    await supabase.update_payout_status(
        transaction_id,
        'SUCCESS',
        transfer_id=transfer_id
    )
    
    logger.info(f"Payout for transaction {transaction_id} completed successfully")

async def handle_transfer_failed(data: dict):
    """
    Handle failed transfer event - payout failed
    """
    transfer_id = data.get('id')
    transaction_id = data.get('reference')
    failure_reason = data.get('reason', 'Unknown failure')
    
    # Update payout status to FAILED
    await supabase.update_payout_status(
        transaction_id,
        'FAILED',
        transfer_id=transfer_id,
        failure_reason=failure_reason
    )
    
    logger.error(f"Payout for transaction {transaction_id} failed: {failure_reason}")