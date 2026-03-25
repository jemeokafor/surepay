import asyncio
import os
import uuid
from dotenv import load_dotenv
from app.core.config import settings

# Load environment variables
load_dotenv()

async def seed_admin_user():
    """Seed the default admin user"""
    try:
        # We need to import supabase here to avoid circular imports
        from app.services.supabase import supabase_service
        
        # Initialize Supabase client
        await supabase_service._ensure_client()
        
        if not supabase_service.client:
            print("Failed to initialize Supabase client")
            return
        
        # Check if admin user already exists
        response = await supabase_service.client.table('vendors').select('*').eq('email', settings.DEFAULT_ADMIN_EMAIL).execute()
        
        if response.data:
            print(f"Admin user {settings.DEFAULT_ADMIN_EMAIL} already exists")
            return
        
        # Generate a random UUID for the admin user
        admin_id = str(uuid.uuid4())
        
        # Create admin user data
        admin_data = {
            'id': admin_id,
            'username': 'admin',
            'display_name': 'System Admin',
            'email': settings.DEFAULT_ADMIN_EMAIL,
            'role': 'super_admin',
            'status': 'active',
            'payout_ready': False,
            'trust_badge_enabled': True
        }
        
        # Insert admin user
        result = await supabase_service.client.table('vendors').insert(admin_data).execute()
        
        if result.data:
            print(f"Successfully created admin user: {settings.DEFAULT_ADMIN_EMAIL}")
            print(f"Admin user ID: {admin_id}")
            print("Please update your .env files with this ID if needed")
        else:
            print("Failed to create admin user")
            
    except Exception as e:
        print(f"Error seeding admin user: {str(e)}")

if __name__ == "__main__":
    asyncio.run(seed_admin_user())