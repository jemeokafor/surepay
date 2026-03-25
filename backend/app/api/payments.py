from fastapi import APIRouter, HTTPException, Request
from app.services import paystack, supabase
from app.core.config import settings
from app.core.security_middleware import (
    rate_limit_payment_initialization, 
    sanitize_input, 
    validate_email, 
    validate_amount
)
from app.core.monitoring import business_analytics, performance_monitor
import uuid
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/initialize")
async def initialize_payment(request: Request, transaction_data: dict):
    """
    Initialize a new payment transaction
    Rate limited to 10 requests per minute per IP
    """
    # Start performance timer
    timer_id = performance_monitor.start_timer("payment_initialization")
    
    try:
        # Validate and sanitize inputs
        amount = transaction_data.get('amount')
        customer_email = transaction_data.get('customer_email')
        vendor_id = transaction_data.get('vendor_id')
        
        # Validate required fields
        if not amount or not customer_email or not vendor_id:
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Validate amount
        if not validate_amount(amount):
            raise HTTPException(status_code=400, detail="Invalid amount")
        
        # Validate email
        if not validate_email(customer_email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        # Sanitize inputs
        sanitized_email = sanitize_input(customer_email)
        sanitized_vendor_id = sanitize_input(vendor_id)
        product_id = transaction_data.get('product_id')
        sanitized_product_id = sanitize_input(product_id) if product_id else None
        
        # Generate unique transaction reference
        transaction_id = str(uuid.uuid4())
        
        # Create transaction in Supabase
        transaction = await supabase.create_transaction(
            transaction_id=transaction_id,
            amount=amount,
            currency=transaction_data.get('currency', 'NGN'),
            vendor_id=sanitized_vendor_id,
            product_id=sanitized_product_id,
            metadata=transaction_data.get('metadata', {})
        )
        
        # Initialize Paystack transaction
        paystack_response = await paystack.initialize_transaction(
            amount=amount,
            email=sanitized_email,
            reference=transaction_id,
            metadata={
                'transaction_id': transaction_id,
                'vendor_id': sanitized_vendor_id
            }
        )
        
        # Update transaction with Paystack details
        await supabase.update_transaction_paystack_details(
            transaction_id,
            paystack_response['data']['authorization_url'],
            paystack_response['data']['access_code']
        )
        
        # End performance timer
        duration = performance_monitor.end_timer(timer_id)
        performance_monitor.log_metric("payment_initialization_duration", duration)
        
        return {
            "status": "success",
            "transaction_id": transaction_id,
            "authorization_url": paystack_response['data']['authorization_url']
        }
        
    except Exception as e:
        logger.error(f"Payment initialization failed: {str(e)}")
        # End performance timer on error
        performance_monitor.end_timer(timer_id)
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/verify/{transaction_id}")
async def verify_payment(transaction_id: str):
    """
    Verify payment status with Paystack
    """
    # Sanitize transaction_id
    sanitized_transaction_id = sanitize_input(transaction_id)
    
    # Start performance timer
    timer_id = performance_monitor.start_timer("payment_verification")
    
    try:
        # Get transaction from Supabase
        transaction = await supabase.get_transaction(sanitized_transaction_id)
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # Verify with Paystack
        verification = await paystack.verify_transaction(sanitized_transaction_id)
        
        # Update transaction status if needed
        if verification['data']['status'] == 'success':
            await supabase.update_transaction_status(
                sanitized_transaction_id, 
                'FUNDS_LOCKED'
            )
            
            # Track successful transaction
            business_analytics.track_transaction(
                amount=transaction.get('amount', 0),
                fee=transaction.get('fee_ngn', 0)
            )
        
        # End performance timer
        duration = performance_monitor.end_timer(timer_id)
        performance_monitor.log_metric("payment_verification_duration", duration)
        
        return verification
        
    except Exception as e:
        logger.error(f"Payment verification failed: {str(e)}")
        # End performance timer on error
        performance_monitor.end_timer(timer_id)
        raise HTTPException(status_code=400, detail=str(e))