from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from app.core.config import settings
from app.services.supabase import supabase_service
import logging

logger = logging.getLogger(__name__)
security = HTTPBearer()

async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get current admin user from JWT token
    """
    try:
        # Decode JWT token
        token = credentials.credentials
        # In a real implementation, we would verify the token with Supabase
        # For now, we'll return a placeholder
        
        # This is a simplified version - in production, you would:
        # 1. Verify the JWT token with Supabase
        # 2. Get the user ID from the token
        # 3. Check if the user has admin role in the database
        # 4. Return the admin user object
        
        # Placeholder implementation
        user_id = "00000000-0000-0000-0000-000000000000"  # This would come from token
        admin_user = await supabase_service.client.table('vendors').select('*').eq('id', user_id).execute()
        
        if not admin_user.data:
            raise HTTPException(status_code=401, detail="Admin user not found")
        
        if admin_user.data[0].get('role') not in ('admin', 'super_admin'):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        return admin_user.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error authenticating admin: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

async def verify_2fa_session(session_id: str, admin_id: str):
    """
    Verify that admin has valid 2FA session
    """
    try:
        response = await supabase_service.client.table('admin_sessions').select('*').eq('id', session_id).execute()
        session = response.data[0] if response.data else None
        
        if not session:
            return False
        
        # Check if session belongs to admin
        if session['user_id'] != admin_id:
            return False
        
        # Check if session is verified and not expired
        from datetime import datetime
        if not session['otp_verified']:
            return False
        
        if datetime.fromisoformat(session['expires_at']) < datetime.utcnow():
            # Delete expired session
            await supabase_service.client.table('admin_sessions').delete().eq('id', session_id).execute()
            return False
        
        return True
    except Exception as e:
        logger.error(f"Error verifying 2FA session {session_id}: {str(e)}")
        return False

async def require_2fa(session_id: str = None, admin = Depends(get_current_admin)):
    """
    Dependency to require 2FA verification for sensitive actions
    """
    if not session_id:
        raise HTTPException(status_code=400, detail="2FA session ID required")
    
    is_valid = await verify_2fa_session(session_id, admin['id'])
    if not is_valid:
        raise HTTPException(status_code=403, detail="2FA verification required or expired")
    
    return admin