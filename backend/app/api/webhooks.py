from fastapi import APIRouter, HTTPException, Header, Request, Depends
from app.core.security import verify_paystack_signature, get_raw_body
from app.core.config import settings
from app.core.security_middleware import rate_limit_webhook, sanitize_input
from app.services import paystack, supabase
from app.core.monitoring import business_analytics, performance_monitor
import json
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/paystack")
@rate_limit_webhook()
async def handle_paystack_webhook(
    request: Request,
    payload: bytes = Depends(get_raw_body),
    signature: str = Header(None, alias="x-paystack-signature")
):
    """
    Handle Paystack webhook events
    Rate limited to 100 requests per minute per IP
    """
    # Start performance timer
    timer_id = performance_monitor.start_timer("webhook_processing")
    
    # Verify signature
    if not verify_paystack_signature(payload, signature):
        logger.warning("Invalid Paystack webhook signature")
        # End performance timer on error
        performance_monitor.end_timer(timer_id)
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Parse payload
    try:
        event_data = json.loads(payload.decode('utf-8'))
        event_type = event_data.get('event')
        data = event_data.get('data', {})
    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook payload")
        # End performance timer on error
        performance_monitor.end_timer(timer_id)
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
    
    # End performance timer
    duration = performance_monitor.end_timer(timer_id)
    performance_monitor.log_metric("webhook_processing_duration", duration)
    
    return {"status": "success"}

async def handle_charge_success(data: dict):
    """
    Handle successful charge event - funds locked
    """
    # Sanitize reference
    reference = sanitize_input(data.get('reference'))
    amount = data.get('amount')
    
    # Update transaction status to FUNDS_LOCKED
    await supabase.update_transaction_status(
        reference, 
        'FUNDS_LOCKED', 
        amount=amount
    )
    
    # Track successful transaction
    business_analytics.track_transaction(
        amount=amount or 0,
        fee=amount * 0.015 if amount else 0  # Assuming 1.5% fee
    )
    
    logger.info(f"Transaction {reference} updated to FUNDS_LOCKED")

async def handle_transfer_success(data: dict):
    """
    Handle successful transfer event - payout completed
    """
    # Sanitize IDs
    transfer_id = sanitize_input(data.get('id'))
    reference = sanitize_input(data.get('reference'))
    
    # Update payout status to SUCCESS
    await supabase.update_payout_status(
        reference,
        'SUCCESS',
        transfer_id=transfer_id
    )
    
    # Track successful payout
    # Get transaction to get amount
    transaction = await supabase.get_transaction(reference)
    if transaction:
        business_analytics.track_payout(
            amount=transaction.get('vendor_net_ngn', 0)
        )
    
    logger.info(f"Payout for transaction {reference} completed successfully")

async def handle_transfer_failed(data: dict):
    """
    Handle failed transfer event - payout failed
    """
    # Sanitize IDs and reason
    transfer_id = sanitize_input(data.get('id'))
    reference = sanitize_input(data.get('reference'))
    failure_reason = sanitize_input(data.get('reason', 'Unknown failure'))
    
    # Update payout status to FAILED
    await supabase.update_payout_status(
        reference,
        'FAILED',
        transfer_id=transfer_id,
        failure_reason=failure_reason
    )
    
    # Track failed payout
    business_analytics.track_dispute(resolution="payout_failed")
    
    logger.error(f"Payout for transaction {reference} failed: {failure_reason}")