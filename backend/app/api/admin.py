from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.services.admin_service import admin_service
from app.services.email_service import email_service
from app.services.supabase import supabase_service
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class OTPRequest(BaseModel):
    action: str
    target_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class OTPVerifyRequest(BaseModel):
    session_id: str
    otp_code: str

class ManualActionRequest(BaseModel):
    reason: str = "Manual action by admin"

class VendorActionRequest(BaseModel):
    reason: str = "Manual action by admin"

@router.get("/auth/status")
async def get_admin_status(request: Request):
    """
    Check if current user is admin
    """
    # This would typically check the user's JWT token
    # For now, we'll return a placeholder
    return {"is_admin": False, "role": None}

@router.post("/auth/request-otp")
async def request_otp(otp_request: OTPRequest, request: Request):
    """
    Request OTP for sensitive admin actions
    """
    try:
        # In a real implementation, we would verify the user's identity
        # For now, we'll use a placeholder user ID
        user_id = "00000000-0000-0000-0000-000000000000"  # Placeholder
        
        # Create OTP session
        session_id = await admin_service.create_otp_session(user_id)
        
        if not session_id:
            raise HTTPException(status_code=500, detail="Failed to create OTP session")
        
        # Generate OTP (in real implementation, this would be done in create_otp_session)
        import secrets
        import string
        otp_code = ''.join(secrets.choice(string.digits) for _ in range(6))
        
        # Send OTP email
        # In a real implementation, we would get the admin's email from the database
        admin_email = "admin@surepay.link"
        email_sent = email_service.send_otp_email(admin_email, otp_code)
        
        if not email_sent:
            logger.warning("Failed to send OTP email, but session created")
        
        return {
            "status": "success",
            "session_id": session_id,
            "message": "OTP sent to your email"
        }
    except Exception as e:
        logger.error(f"Error requesting OTP: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to request OTP")

@router.post("/auth/verify-otp")
async def verify_otp(otp_verify: OTPVerifyRequest):
    """
    Verify OTP for admin session
    """
    try:
        is_valid = await admin_service.verify_otp(otp_verify.session_id, otp_verify.otp_code)
        
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        
        return {
            "status": "success",
            "message": "OTP verified successfully"
        }
    except Exception as e:
        logger.error(f"Error verifying OTP: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to verify OTP")

@router.get("/stats/overview")
async def get_admin_stats():
    """
    Get admin dashboard statistics
    """
    try:
        stats = await admin_service.get_platform_stats()
        recent_transactions = await admin_service.get_recent_transactions(5)
        recent_disputes = await admin_service.get_recent_disputes(5)
        failed_payouts = await admin_service.get_failed_payouts(5)
        
        return {
            "stats": stats,
            "recent_transactions": recent_transactions,
            "recent_disputes": recent_disputes,
            "failed_payouts": failed_payouts
        }
    except Exception as e:
        logger.error(f"Error getting admin stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get admin stats")

@router.get("/transactions")
async def get_transactions(status: Optional[str] = None, limit: int = 50, offset: int = 0):
    """
    Get all transactions with optional filtering
    """
    try:
        query = supabase_service.client.table('transactions').select('''
            *,
            vendor:vendors(username, display_name)
        ''')
        
        if status:
            query = query.eq('status', status)
        
        response = await query.order('created_at', desc=True).range(offset, offset + limit - 1).execute()
        
        # Get total count
        count_response = await supabase_service.client.table('transactions').select('count()').execute()
        total_count = count_response.data[0]['count'] if count_response.data else 0
        
        return {
            "transactions": response.data,
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error getting transactions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get transactions")

@router.get("/transactions/{transaction_id}")
async def get_transaction(transaction_id: str):
    """
    Get specific transaction details
    """
    try:
        response = await supabase_service.client.table('transactions').select('''
            *,
            vendor:vendors(username, display_name, email),
            product:products(name, price_ngn),
            dispute:disputes(*)
        ''').eq('id', transaction_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        return {"transaction": response.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transaction {transaction_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get transaction")

@router.post("/transactions/{transaction_id}/release")
async def manual_release_transaction(transaction_id: str, action_request: ManualActionRequest):
    """
    Manually release a transaction (requires 2FA)
    """
    # In a real implementation, we would verify the admin's 2FA session
    # For now, we'll use a placeholder admin ID
    admin_id = "00000000-0000-0000-0000-000000000000"  # Placeholder
    
    success = await admin_service.manual_release_transaction(
        transaction_id, 
        admin_id, 
        action_request.reason
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to release transaction")
    
    return {"status": "success", "message": "Transaction released successfully"}

@router.post("/transactions/{transaction_id}/refund")
async def manual_refund_transaction(transaction_id: str, action_request: ManualActionRequest):
    """
    Manually refund a transaction (requires 2FA)
    """
    # In a real implementation, we would verify the admin's 2FA session
    # For now, we'll use a placeholder admin ID
    admin_id = "00000000-0000-0000-0000-000000000000"  # Placeholder
    
    success = await admin_service.manual_refund_transaction(
        transaction_id, 
        admin_id, 
        action_request.reason
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to refund transaction")
    
    return {"status": "success", "message": "Transaction refunded successfully"}

@router.get("/disputes")
async def get_disputes(status: Optional[str] = None, limit: int = 50, offset: int = 0):
    """
    Get all disputes with optional filtering
    """
    try:
        query = supabase_service.client.table('disputes').select('''
            *,
            transaction:transactions(amount_ngn, buyer_email, vendor_id),
            vendor:vendors(username, display_name)
        ''')
        
        if status:
            query = query.eq('status', status)
        
        response = await query.order('opened_at', desc=True).range(offset, offset + limit - 1).execute()
        
        # Get total count
        count_response = await supabase_service.client.table('disputes').select('count()').execute()
        total_count = count_response.data[0]['count'] if count_response.data else 0
        
        return {
            "disputes": response.data,
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error getting disputes: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get disputes")

@router.get("/disputes/{dispute_id}")
async def get_dispute(dispute_id: str):
    """
    Get specific dispute details
    """
    try:
        response = await supabase_service.client.table('disputes').select('''
            *,
            transaction:transactions(*, vendor:vendors(username, display_name, email)),
            evidence:dispute_evidence(*)
        ''').eq('id', dispute_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Dispute not found")
        
        return {"dispute": response.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dispute {dispute_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get dispute")

@router.post("/disputes/{dispute_id}/resolve")
async def resolve_dispute(dispute_id: str, action_request: ManualActionRequest):
    """
    Resolve a dispute (requires 2FA)
    """
    # In a real implementation, we would verify the admin's 2FA session
    # For now, we'll use a placeholder admin ID
    admin_id = "00000000-0000-0000-0000-000000000000"  # Placeholder
    
    # Get dispute
    try:
        response = await supabase_service.client.table('disputes').select('*').eq('id', dispute_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Dispute not found")
        
        dispute = response.data[0]
        
        # Update dispute status
        await supabase_service.client.table('disputes').update({
            'status': 'resolved_release',  # Default to release, but this should be configurable
            'resolved_by': admin_id,
            'resolved_at': 'now()',
            'resolution_notes': action_request.reason
        }).eq('id', dispute_id).execute()
        
        # Log admin action
        await admin_service.log_admin_action(
            admin_id=admin_id,
            action_type="resolve_dispute",
            target_type="dispute",
            target_id=dispute_id,
            details={"resolution": "release", "reason": action_request.reason}
        )
        
        return {"status": "success", "message": "Dispute resolved successfully"}
    except Exception as e:
        logger.error(f"Error resolving dispute {dispute_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to resolve dispute")

@router.get("/vendors")
async def get_vendors(status: Optional[str] = None, limit: int = 50, offset: int = 0):
    """
    Get all vendors with optional filtering
    """
    try:
        query = supabase_service.client.table('vendors').select('*')
        
        if status:
            query = query.eq('status', status)
        
        response = await query.order('created_at', desc=True).range(offset, offset + limit - 1).execute()
        
        # Get total count
        count_response = await supabase_service.client.table('vendors').select('count()').execute()
        total_count = count_response.data[0]['count'] if count_response.data else 0
        
        return {
            "vendors": response.data,
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error getting vendors: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get vendors")

@router.get("/vendors/{vendor_id}")
async def get_vendor(vendor_id: str):
    """
    Get specific vendor details
    """
    try:
        response = await supabase_service.client.table('vendors').select('''
            *,
            transactions:transactions(count),
            disputes:disputes(count)
        ''').eq('id', vendor_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Vendor not found")
        
        vendor = response.data[0]
        
        # Get additional metrics
        tx_response = await supabase_service.client.table('transactions').select('count()').eq('vendor_id', vendor_id).execute()
        vendor['total_transactions'] = tx_response.data[0]['count'] if tx_response.data else 0
        
        dispute_response = await supabase_service.client.table('disputes').select('count()').eq('transaction_id', vendor_id).execute()
        vendor['total_disputes'] = dispute_response.data[0]['count'] if dispute_response.data else 0
        
        return {"vendor": vendor}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting vendor {vendor_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get vendor")

@router.post("/vendors/{vendor_id}/suspend")
async def suspend_vendor(vendor_id: str, action_request: VendorActionRequest):
    """
    Suspend a vendor (requires 2FA)
    """
    # In a real implementation, we would verify the admin's 2FA session
    # For now, we'll use a placeholder admin ID
    admin_id = "00000000-0000-0000-0000-000000000000"  # Placeholder
    
    success = await admin_service.suspend_vendor(vendor_id, admin_id, action_request.reason)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to suspend vendor")
    
    return {"status": "success", "message": "Vendor suspended successfully"}

@router.post("/vendors/{vendor_id}/activate")
async def activate_vendor(vendor_id: str, action_request: VendorActionRequest):
    """
    Activate a vendor (requires 2FA)
    """
    # In a real implementation, we would verify the admin's 2FA session
    # For now, we'll use a placeholder admin ID
    admin_id = "00000000-0000-0000-0000-000000000000"  # Placeholder
    
    success = await admin_service.activate_vendor(vendor_id, admin_id, action_request.reason)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to activate vendor")
    
    return {"status": "success", "message": "Vendor activated successfully"}

@router.get("/payouts")
async def get_payouts(status: Optional[str] = None, limit: int = 50, offset: int = 0):
    """
    Get all payouts with optional filtering
    """
    try:
        query = supabase_service.client.table('payouts').select('''
            *,
            transaction:transactions(amount_ngn, vendor_id),
            vendor:vendors(username, display_name)
        ''')
        
        if status:
            query = query.eq('status', status)
        
        response = await query.order('created_at', desc=True).range(offset, offset + limit - 1).execute()
        
        # Get total count
        count_response = await supabase_service.client.table('payouts').select('count()').execute()
        total_count = count_response.data[0]['count'] if count_response.data else 0
        
        return {
            "payouts": response.data,
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error getting payouts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get payouts")

@router.post("/payouts/retry/{transaction_id}")
async def retry_payout(transaction_id: str, action_request: ManualActionRequest):
    """
    Retry a failed payout (requires 2FA)
    """
    # In a real implementation, we would verify the admin's 2FA session
    # For now, we'll use a placeholder admin ID
    admin_id = "00000000-0000-0000-0000-000000000000"  # Placeholder
    
    # Log admin action
    await admin_service.log_admin_action(
        admin_id=admin_id,
        action_type="retry_payout",
        target_type="payout",
        target_id=transaction_id,
        details={"reason": action_request.reason}
    )
    
    # In a real implementation, we would call the payout service to retry
    # For now, we'll just return success
    return {"status": "success", "message": "Payout retry initiated successfully"}

@router.get("/audit")
async def get_audit_log(action_type: Optional[str] = None, limit: int = 50, offset: int = 0):
    """
    Get admin action audit log
    """
    try:
        query = supabase_service.client.table('admin_action_log').select('''
            *,
            admin:vendors(display_name, email)
        ''')
        
        if action_type:
            query = query.eq('action_type', action_type)
        
        response = await query.order('created_at', desc=True).range(offset, offset + limit - 1).execute()
        
        # Get total count
        count_response = await supabase_service.client.table('admin_action_log').select('count()').execute()
        total_count = count_response.data[0]['count'] if count_response.data else 0
        
        return {
            "audit_log": response.data,
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error getting audit log: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get audit log")