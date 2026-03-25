#!/usr/bin/env python3
"""
Test script to verify backend components
"""

import os
import sys
import asyncio

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# Set only the environment variables needed for backend
os.environ['SUPABASE_URL'] = os.environ.get('SUPABASE_URL', '')
os.environ['SUPABASE_SERVICE_ROLE_KEY'] = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
os.environ['PAYSTACK_SECRET_KEY'] = os.environ.get('PAYSTACK_SECRET_KEY', '')
os.environ['PAYSTACK_WEBHOOK_SECRET'] = os.environ.get('PAYSTACK_WEBHOOK_SECRET', '')
os.environ['FRONTEND_URL'] = os.environ.get('FRONTEND_URL', 'http://localhost:3000')

def test_config():
    """Test configuration loading"""
    print("Testing configuration...")
    
    # Import after setting environment variables
    from backend.app.core.config import settings
    
    print(f"Supabase URL configured: {bool(settings.SUPABASE_URL)}")
    print(f"Paystack secret key configured: {bool(settings.PAYSTACK_SECRET_KEY)}")
    print(f"Frontend URL: {settings.FRONTEND_URL}")

def test_imports():
    """Test importing backend modules"""
    print("\nTesting imports...")
    try:
        from backend.app.core.config import settings
        print("✓ Config import successful")
    except Exception as e:
        print(f"✗ Config import failed: {e}")
        
    try:
        from backend.app.services import supabase
        print("✓ Supabase service import successful")
    except Exception as e:
        print(f"✗ Supabase service import failed: {e}")
        
    try:
        from backend.app.services import paystack
        print("✓ Paystack service import successful")
    except Exception as e:
        print(f"✗ Paystack service import failed: {e}")

def main():
    """Main test function"""
    print("SurePay Backend Test Suite")
    print("=" * 30)
    
    test_config()
    test_imports()
    
    print("\nTest completed.")

if __name__ == "__main__":
    main()