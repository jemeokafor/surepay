#!/usr/bin/env python3
"""
Admin User Seeding Script
Run this script to create the default admin user in the database.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv
import uuid

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

# Load environment variables
load_dotenv()

async def seed_admin_user():
    """Seed the default admin user"""
    try:
        # Import the Supabase client
        from supabase import create_client
        
        # Get Supabase configuration from environment
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not supabase_url or not supabase_service_key:
            print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment")
            return
        
        # Create Supabase client
        supabase = create_client(supabase_url, supabase_service_key)
        
        # Get admin configuration
        admin_email = os.getenv('DEFAULT_ADMIN_EMAIL', 'admin@surepay.link')
        admin_password = os.getenv('DEFAULT_ADMIN_PASSWORD', 'Admin123!')
        
        # Check if admin user already exists
        response = supabase.table('vendors').select('*').eq('email', admin_email).execute()
        
        if response.data:
            print(f"Admin user {admin_email} already exists")
            return
        
        # Generate a random UUID for the admin user
        admin_id = str(uuid.uuid4())
        
        # Create admin user data
        admin_data = {
            'id': admin_id,
            'username': 'admin',
            'display_name': 'System Admin',
            'email': admin_email,
            'role': 'super_admin',
            'status': 'active',
            'payout_ready': False,
            'trust_badge_enabled': True
        }
        
        # Insert admin user
        result = supabase.table('vendors').insert(admin_data).execute()
        
        if result.data:
            print(f"Successfully created admin user: {admin_email}")
            print(f"Admin user ID: {admin_id}")
            print("Please update your .env files with this ID if needed")
        else:
            print("Failed to create admin user")
            
    except Exception as e:
        print(f"Error seeding admin user: {str(e)}")

if __name__ == "__main__":
    asyncio.run(seed_admin_user())