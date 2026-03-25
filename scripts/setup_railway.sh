#!/bin/bash

# SurePay Railway Backend Environment Setup Script
# This script sets up all required environment variables on Railway

echo "🚀 Setting up SurePay Backend on Railway..."
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null
then
    echo "❌ Railway CLI is not installed. Please install it first:"
    echo "   npm install -g @railway/cli"
    exit 1
fi

# Check if user is logged in
echo "Checking Railway authentication..."
if ! railway whoami &> /dev/null
then
    echo "❌ Not logged in to Railway. Please run:"
    echo "   railway login"
    exit 1
fi

echo "✅ Authenticated with Railway"
echo ""

# Environment variables to set
declare -A ENV_VARS=(
    # Supabase Configuration
    ["SUPABASE_URL"]="https://your-project.supabase.co"
    ["SUPABASE_SERVICE_ROLE_KEY"]="your-service-role-key"
    
    # Paystack Configuration
    ["PAYSTACK_SECRET_KEY"]="sk_test_your_secret_key"
    ["PAYSTACK_WEBHOOK_SECRET"]="your_webhook_secret"
    
    # Frontend Configuration
    ["FRONTEND_URL"]="https://surepay.vercel.app"
    ["API_URL"]="https://surepay-backend.railway.app"
    
    # Email Configuration (Resend)
    ["RESEND_API_KEY"]="re_NhihqPVs_NqK5fws34VjGweSRPddhUutM"
    ["EMAIL_FROM"]="noreply@surepay.link"
    ["EMAIL_FROM_NAME"]="SurePay"
    
    # Admin Configuration
    ["DEFAULT_ADMIN_EMAIL"]="admin@surepay.link"
    ["DEFAULT_ADMIN_PASSWORD"]="Admin123!"
    
    # Environment
    ["ENVIRONMENT"]="production"
)

# Set environment variables
echo "Setting environment variables..."
for key in "${!ENV_VARS[@]}"; do
    value="${ENV_VARS[$key]}"
    echo "Setting $key..."
    railway variables set "$key"="$value"
done

echo ""
echo "✅ Environment variables set successfully!"
echo ""
echo "Next steps:"
echo "1. Update the following variables with your actual values:"
echo "   - SUPABASE_URL"
echo "   - SUPABASE_SERVICE_ROLE_KEY"
echo "   - PAYSTACK_SECRET_KEY"
echo "   - PAYSTACK_WEBHOOK_SECRET"
echo ""
echo "2. Deploy your backend:"
echo "   railway up"
echo ""
echo "3. Run the database migration:"
echo "   - Execute supabase/migrations/0003_admin_role.sql in your Supabase dashboard"
echo ""
echo "4. Seed the admin user:"
echo "   railway run python scripts/seed_admin_user.py"
echo ""
echo "🎉 Setup complete!"