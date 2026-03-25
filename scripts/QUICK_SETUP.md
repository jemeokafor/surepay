# Quick Railway Setup - Manual Steps

## Step 1: Login to Railway
```bash
railway login
```

## Step 2: Create/Link Project
```bash
railway init
# or if project exists:
railway link
```

## Step 3: Set Environment Variables

Run these commands one by one:

```bash
# Supabase (UPDATE THESE VALUES)
railway variables set SUPABASE_URL=https://your-project.supabase.co
railway variables set SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Paystack (UPDATE THESE VALUES)
railway variables set PAYSTACK_SECRET_KEY=sk_test_your_secret_key
railway variables set PAYSTACK_WEBHOOK_SECRET=your_webhook_secret

# Frontend
railway variables set FRONTEND_URL=https://surepay.vercel.app
railway variables set API_URL=https://surepay-backend.railway.app

# Email (Resend API Key provided)
railway variables set RESEND_API_KEY=re_NhihqPVs_NqK5fws34VjGweSRPddhUutM
railway variables set EMAIL_FROM=noreply@surepay.link
railway variables set EMAIL_FROM_NAME=SurePay

# Admin
railway variables set DEFAULT_ADMIN_EMAIL=admin@surepay.link
railway variables set DEFAULT_ADMIN_PASSWORD=Admin123!

# Environment
railway variables set ENVIRONMENT=production
```

## Step 4: Deploy
```bash
cd backend
railway up
```

## Step 5: Generate Domain
```bash
railway domain
```

## Step 6: Update API_URL
```bash
railway variables set API_URL=https://your-generated-domain.railway.app
```

## Step 7: Run Database Migration
Go to Supabase Dashboard → SQL Editor → Run:
- `supabase/migrations/0001_surepay_initial_schema.sql`
- `supabase/migrations/0002_security_functions.sql`
- `supabase/migrations/0003_admin_role.sql`

## Step 8: Seed Admin User
```bash
railway run python scripts/seed_admin_user.py
```

## Step 9: Verify
```bash
railway logs
curl https://your-domain.railway.app/health
```

## Done! 🎉

Your backend should now be running at: https://your-domain.railway.app

Admin credentials:
- Email: admin@surepay.link
- Password: Admin123!

⚠️ **IMPORTANT**: Change the admin password after first login!