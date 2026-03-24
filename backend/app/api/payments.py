from fastapi import APIRouter, HTTPException, Request
from app.services import paystack, supabase
from app.core.config import settings
import uuid
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/initialize")
async def initialize_payment(transaction_data: dict):
    """
    Initialize a new payment transaction
    """
    try:
        # Generate unique transaction reference
        transaction_id = str(uuid.uuid4())
        
        # Create transaction in Supabase
        transaction = await supabase.create_transaction(
            transaction_id=transaction_id,
            amount=transaction_data['amount'],
            currency=transaction_data.get('currency', 'NGN'),
            vendor_id=transaction_data['vendor_id'],
            product_id=transaction_data.get('product_id'),
            metadata=transaction_data.get('metadata', {})
        )
        
        # Initialize Paystack transaction
        paystack_response = await paystack.initialize_transaction(
            amount=transaction_data['amount'],
            email=transaction_data['customer_email'],
            reference=transaction_id,
            metadata={
                'transaction_id': transaction_id,
                'vendor_id': transaction_data['vendor_id']
            }
        )
        
        # Update transaction with Paystack details
        await supabase.update_transaction_paystack_details(
            transaction_id,
            paystack_response['data']['authorization_url'],
            paystack_response['data']['access_code']
        )
        
        return {
            "status": "success",
            "transaction_id": transaction_id,
            "authorization_url": paystack_response['data']['authorization_url']
        }
        
    except Exception as e:
        logger.error(f"Payment initialization failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/verify/{transaction_id}")
async def verify_payment(transaction_id: str):
    """
    Verify payment status with Paystack
    """
    try:
        # Get transaction from Supabase
        transaction = await supabase.get_transaction(transaction_id)
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # Verify with Paystack
        verification = await paystack.verify_transaction(transaction_id)
        
        # Update transaction status if needed
        if verification['data']['status'] == 'success':
            await supabase.update_transaction_status(
                transaction_id, 
                'FUNDS_LOCKED'
            )
        
        return verification
        
    except Exception as e:
        logger.error(f"Payment verification failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))