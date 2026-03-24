from fastapi import APIRouter, HTTPException
from app.core.config import settings

router = APIRouter()

@router.get("/")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "SurePay Backend API"
    }

@router.get("/supabase")
async def supabase_health():
    """
    Check Supabase connection
    """
    try:
        # Test Supabase connection
        from app.services import supabase
        health = await supabase.get_health()
        return {"status": "healthy", "supabase": health}
    except Exception as e:
        return {"status": "unhealthy", "supabase": str(e)}

@router.get("/paystack")
async def paystack_health():
    """
    Check Paystack API connectivity
    """
    try:
        # Test Paystack connection
        from app.services import paystack
        health = await paystack.get_health()
        return {"status": "healthy", "paystack": health}
    except Exception as e:
        return {"status": "unhealthy", "paystack": str(e)}