from app.core.config import settings
from app.services.supabase import supabase_service
from app.core.security import verify_paystack_signature
import logging
import secrets
import string
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import resend

logger = logging.getLogger(__name__)

class AdminService:
    def __init__(self):
        self.supabase = supabase_service
        self.resend_client = None
        if settings.RESEND_API_KEY:
            resend.api_key = settings.RESEND_API_KEY
            self.resend_client = resend
    
    async def get_admin_user(self, user_id: str) -> Optional[Dict[Any, Any]]:
        """
        Get admin user with role verification
        """
        try:
            response = await self.supabase.client.table('vendors').select('*').eq('id', user_id).execute()
            user = response.data[0] if response.data else None
            
            if user and user.get('role') in ('admin', 'super_admin'):
                return user
            return None
        except Exception as e:
            logger.error(f"Error getting admin user {user_id}: {str(e)}")
            return None
    
    async def create_otp_session(self, user_id: str) -> Optional[str]:
        """
        Create a new OTP session for admin actions
        """
        try:
            # Generate 6-digit OTP
            otp = ''.join(secrets.choice(string.digits) for _ in range(6))
            
            # Create session record
            session_data = {
                'user_id': user_id,
                'otp_code': otp,  # In production, this should be hashed
                'expires_at': (datetime.utcnow() + timedelta(minutes=5)).isoformat()
            }
            
            response = await self.supabase.client.table('admin_sessions').insert(session_data).execute()
            session_id = response.data[0]['id'] if response.data else None
            
            return session_id
        except Exception as e:
            logger.error(f"Error creating OTP session for user {user_id}: {str(e)}")
            return None
    
    async def verify_otp(self, session_id: str, otp_code: str) -> bool:
        """
        Verify OTP code for admin session
        """
        try:
            # Get session
            response = await self.supababse.client.table('admin_sessions').select('*').eq('id', session_id).execute()
            session = response.data[0] if response.data else None
            
            if not session:
                return False
            
            # Check if expired
            if datetime.fromisoformat(session['expires_at']) < datetime.utcnow():
                # Delete expired session
                await self.supabase.client.table('admin_sessions').delete().eq('id', session_id).execute()
                return False
            
            # Verify OTP
            if session['otp_code'] == otp_code:
                # Mark as verified
                await self.supabase.client.table('admin_sessions').update({
                    'otp_verified': True
                }).eq('id', session_id).execute()
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error verifying OTP for session {session_id}: {str(e)}")
            return False
    
    async def send_otp_email(self, email: str, otp_code: str) -> bool:
        """
        Send OTP code to admin email
        """
        if not self.resend_client:
            logger.error("Resend client not configured")
            return False
        
        try:
            params = {
                "from": f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>",
                "to": [email],
                "subject": "SurePay Admin - Security Code",
                "html": f"""
                <h2>Admin Security Code</h2>
                <p>Your security code for this admin action is:</p>
                <h1 style="font-size: 32px; letter-spacing: 8px;">{otp_code}</h1>
                <p>This code will expire in 5 minutes.</p>
                <p>If you did not request this code, please contact security immediately.</p>
                """
            }
            
            resend.Emails.send(params)
            return True
        except Exception as e:
            logger.error(f"Error sending OTP email to {email}: {str(e)}")
            return False
    
    async def log_admin_action(self, admin_id: str, action_type: str, target_type: str = None, 
                              target_id: str = None, details: Dict = None) -> bool:
        """
        Log admin action to audit trail
        """
        try:
            action_data = {
                'admin_id': admin_id,
                'action_type': action_type,
                'target_type': target_type,
                'target_id': target_id,
                'details': details or {}
            }
            
            await self.supabase.client.table('admin_action_log').insert(action_data).execute()
            return True
        except Exception as e:
            logger.error(f"Error logging admin action for admin {admin_id}: {str(e)}")
            return False
    
    async def get_platform_stats(self) -> Dict[str, Any]:
        """
        Get platform-wide statistics for admin dashboard
        """
        try:
            # Get total transactions count
            tx_response = await self.supabase.client.table('transactions').select('count()').execute()
            total_transactions = tx_response.data[0]['count'] if tx_response.data else 0
            
            # Get total vendors count
            vendor_response = await self.supabase.client.table('vendors').select('count()').execute()
            total_vendors = vendor_response.data[0]['count'] if vendor_response.data else 0
            
            # Get disputed transactions count
            dispute_response = await self.supabase.client.table('disputes').select('count()').execute()
            total_disputes = dispute_response.data[0]['count'] if dispute_response.data else 0
            
            # Get failed payouts count
            payout_response = await self.supabase.client.table('payouts').select('count()').eq('status', 'failed').execute()
            failed_payouts = payout_response.data[0]['count'] if payout_response.data else 0
            
            return {
                'total_transactions': total_transactions,
                'total_vendors': total_vendors,
                'total_disputes': total_disputes,
                'failed_payouts': failed_payouts
            }
        except Exception as e:
            logger.error(f"Error getting platform stats: {str(e)}")
            return {
                'total_transactions': 0,
                'total_vendors': 0,
                'total_disputes': 0,
                'failed_payouts': 0
            }
    
    async def get_recent_transactions(self, limit: int = 10) -> list:
        """
        Get recent transactions for admin dashboard
        """
        try:
            response = await self.supabase.client.table('transactions').select('''
                *,
                vendor:vendors(username, display_name)
            ''').order('created_at', desc=True).limit(limit).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error getting recent transactions: {str(e)}")
            return []
    
    async def get_recent_disputes(self, limit: int = 10) -> list:
        """
        Get recent disputes for admin dashboard
        """
        try:
            response = await self.supabase.client.table('disputes').select('''
                *,
                transaction:transactions(amount_ngn, buyer_email)
            ''').order('opened_at', desc=True).limit(limit).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error getting recent disputes: {str(e)}")
            return []
    
    async def get_failed_payouts(self, limit: int = 10) -> list:
        """
        Get failed payouts for admin dashboard
        """
        try:
            response = await self.supabase.client.table('payouts').select('''
                *,
                transaction:transactions(amount_ngn, vendor_id),
                vendor:vendors(username, display_name)
            ''').eq('status', 'failed').order('updated_at', desc=True).limit(limit).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error getting failed payouts: {str(e)}")
            return []
    
    async def manual_release_transaction(self, transaction_id: str, admin_id: str, reason: str = "Manual release") -> bool:
        """
        Manually release a transaction (admin only)
        """
        try:
            # Get transaction
            tx_response = await self.supabase.client.table('transactions').select('*').eq('id', transaction_id).execute()
            transaction = tx_response.data[0] if tx_response.data else None
            
            if not transaction:
                raise Exception("Transaction not found")
            
            # Check if transaction can be released
            if transaction['status'] not in ('AWAITING_BUYER_CONFIRMATION', 'DISPUTED'):
                raise Exception("Transaction cannot be manually released in current state")
            
            # Update transaction status
            await self.supabase.client.table('transactions').update({
                'status': 'RELEASED',
                'released_at': datetime.utcnow().isoformat()
            }).eq('id', transaction_id).execute()
            
            # Log admin action
            await self.log_admin_action(
                admin_id=admin_id,
                action_type="manual_release",
                target_type="transaction",
                target_id=transaction_id,
                details={"reason": reason, "previous_status": transaction['status']}
            )
            
            return True
        except Exception as e:
            logger.error(f"Error manually releasing transaction {transaction_id}: {str(e)}")
            return False
    
    async def manual_refund_transaction(self, transaction_id: str, admin_id: str, reason: str = "Manual refund") -> bool:
        """
        Manually refund a transaction (admin only)
        """
        try:
            # Get transaction
            tx_response = await self.supabase.client.table('transactions').select('*').eq('id', transaction_id).execute()
            transaction = tx_response.data[0] if tx_response.data else None
            
            if not transaction:
                raise Exception("Transaction not found")
            
            # Check if transaction can be refunded
            if transaction['status'] not in ('FUNDS_LOCKED', 'AWAITING_BUYER_CONFIRMATION', 'DISPUTED'):
                raise Exception("Transaction cannot be manually refunded in current state")
            
            # Update transaction status
            await self.supabase.client.table('transactions').update({
                'status': 'REFUNDED',
                'refunded_at': datetime.utcnow().isoformat()
            }).eq('id', transaction_id).execute()
            
            # Log admin action
            await self.log_admin_action(
                admin_id=admin_id,
                action_type="manual_refund",
                target_type="transaction",
                target_id=transaction_id,
                details={"reason": reason, "previous_status": transaction['status']}
            )
            
            return True
        except Exception as e:
            logger.error(f"Error manually refunding transaction {transaction_id}: {str(e)}")
            return False
    
    async def suspend_vendor(self, vendor_id: str, admin_id: str, reason: str = "Manual suspension") -> bool:
        """
        Suspend a vendor account (admin only)
        """
        try:
            # Update vendor status
            await self.supabase.client.table('vendors').update({
                'status': 'suspended'
            }).eq('id', vendor_id).execute()
            
            # Log admin action
            await self.log_admin_action(
                admin_id=admin_id,
                action_type="suspend_vendor",
                target_type="vendor",
                target_id=vendor_id,
                details={"reason": reason}
            )
            
            return True
        except Exception as e:
            logger.error(f"Error suspending vendor {vendor_id}: {str(e)}")
            return False
    
    async def activate_vendor(self, vendor_id: str, admin_id: str, reason: str = "Manual activation") -> bool:
        """
        Activate a vendor account (admin only)
        """
        try:
            # Update vendor status
            await self.supabase.client.table('vendors').update({
                'status': 'active'
            }).eq('id', vendor_id).execute()
            
            # Log admin action
            await self.log_admin_action(
                admin_id=admin_id,
                action_type="activate_vendor",
                target_type="vendor",
                target_id=vendor_id,
                details={"reason": reason}
            )
            
            return True
        except Exception as e:
            logger.error(f"Error activating vendor {vendor_id}: {str(e)}")
            return False

# Create singleton instance
admin_service = AdminService()