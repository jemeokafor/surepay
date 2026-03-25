from fastapi import APIRouter, HTTPException
from app.core.config import settings
from app.services import supabase, paystack
from app.core.monitoring import get_system_metrics, business_analytics
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/")
async def health_check():
    """
    Basic health check endpoint
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
        health = await supabase.get_health()
        return {"status": "healthy", "supabase": health}
    except Exception as e:
        logger.error(f"Supabase health check failed: {str(e)}")
        return {"status": "unhealthy", "supabase": str(e)}

@router.get("/paystack")
async def paystack_health():
    """
    Check Paystack API connectivity
    """
    try:
        # Test Paystack connection
        health = await paystack.get_health()
        return {"status": "healthy", "paystack": health}
    except Exception as e:
        logger.error(f"Paystack health check failed: {str(e)}")
        return {"status": "unhealthy", "paystack": str(e)}

@router.get("/all")
async def full_health_check():
    """
    Comprehensive health check for all services
    """
    try:
        supabase_health = await supabase.get_health()
        paystack_health = await paystack.get_health()
        
        # Get system metrics
        system_metrics = get_system_metrics()
        
        # Get business analytics
        analytics = business_analytics.get_analytics_summary()
        
        return {
            "status": "healthy" if (supabase_health == "connected" and paystack_health == "connected") else "unhealthy",
            "services": {
                "supabase": supabase_health,
                "paystack": paystack_health
            },
            "system": system_metrics,
            "analytics": analytics,
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Full health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "version": "1.0.0"
        }

@router.get("/metrics")
async def metrics_endpoint():
    """
    System metrics endpoint for monitoring
    """
    try:
        system_metrics = get_system_metrics()
        analytics = business_analytics.get_analytics_summary()
        
        return {
            "system": system_metrics,
            "analytics": analytics,
            "timestamp": analytics["timestamp"]
        }
    except Exception as e:
        logger.error(f"Metrics endpoint failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))