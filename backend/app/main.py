from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.core.config import settings
from app.core.security_middleware import add_security_middleware
from app.core.monitoring import setup_monitoring, alert_system
from app.api import webhooks, payments, payouts, health, admin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Setup monitoring
setup_monitoring(
    sentry_dsn=os.environ.get("SENTRY_DSN"),
    environment=os.environ.get("ENVIRONMENT", "development")
)

# Create FastAPI app
app = FastAPI(
    title="SurePay API",
    description="Backend API for SurePay - Protected payments for social commerce",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add security middleware
add_security_middleware(app)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL] if settings.FRONTEND_URL else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Include API routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])
app.include_router(payments.router, prefix="/api/payments", tags=["payments"])
app.include_router(payouts.router, prefix="/api/payouts", tags=["payouts"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

@app.get("/")
async def root():
    return {"message": "SurePay API is running"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler
    """
    logger.error(f"Global exception handler caught: {str(exc)}")
    
    # Check system health and send alerts if needed
    alert_system.check_system_health()
    
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "message": str(exc)}
    )

@app.on_event("startup")
async def startup_event():
    """
    Startup event handler
    """
    logger.info("Starting SurePay API")
    logger.info(f"Frontend URL: {settings.FRONTEND_URL}")
    logger.info(f"API URL: {settings.API_URL}")
    
    # Log environment variable status
    if settings.SUPABASE_URL:
        logger.info("Supabase URL configured")
    else:
        logger.warning("Supabase URL not configured")
        
    if settings.PAYSTACK_SECRET_KEY:
        logger.info("Paystack secret key configured")
    else:
        logger.warning("Paystack secret key not configured")
        
    if settings.RESEND_API_KEY:
        logger.info("Resend API key configured")
    else:
        logger.warning("Resend API key not configured")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Shutdown event handler
    """
    logger.info("Shutting down SurePay API")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )