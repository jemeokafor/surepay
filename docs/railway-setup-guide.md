# SurePay Railway Backend Setup Guide

This guide will help you set up the SurePay backend on Railway with all required environment variables.

## Prerequisites

1. Railway CLI installed (`npm install -g @railway/cli`)
2. Railway account (https://railway.app)
3. Supabase project (https://supabase.com)
4. Paystack account (https://paystack.com)
5. Resend API key (https://resend.com)

## Step 1: Login to Railway

```bash
railway login
```

Follow the browser authentication flow.

## Step 2: Create a New Project

```bash
railway init
```

Choose "Empty project" and name it "SurePay Backend".

## Step 3: Set Environment Variables

### Option A: Using the setup script

```bash
./scripts/setup_railway.sh
```

### Option B: Setting variables manually

Set each environment variable using the Railway CLI:

```bash
# Supabase Configuration
railway variables set SUPABASE_URL=https://your-project.supabase.co
railway variables set SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Paystack Configuration
railway variables set PAYSTACK_SECRET_KEY=sk_test_your_secret_key
railway variables set PAYSTACK_WEBHOOK_SECRET=your_webhook_secret

# Frontend Configuration
railway variables set FRONTEND_URL=https://surepay.vercel.app
railway variables set API_URL=https://surepay-backend.railway.app

# Email Configuration (Resend)
railway variables set RESEND_API_KEY=re_NhihqPVs_NqK5fws34VjGweSRPddhUutM
railway variables set EMAIL_FROM=noreply@surepay.link
railway variables set EMAIL_FROM_NAME=SurePay

# Admin Configuration
railway variables set DEFAULT_ADMIN_EMAIL=admin@surepay.link
railway variables set DEFAULT_ADMIN_PASSWORD=Admin123!

# Environment
railway variables set ENVIRONMENT=production
```

## Step 4: Deploy the Backend

```bash
# Navigate to the backend directory
cd backend

# Deploy to Railway
railway up
```

## Step 5: Generate a Domain

```bash
railway domain
```

This will generate a public URL for your backend (e.g., `https://surepay-backend.railway.app`).

## Step 6: Update Environment Variables

After generating the domain, update the `API_URL` variable:

```bash
railway variables set API_URL=https://your-railway-domain.railway.app
```

## Step 7: Run Database Migrations

1. Go to your Supabase dashboard
2. Navigate to SQL Editor
3. Execute the following migration files in order:
   - `supabase/migrations/0001_surepay_initial_schema.sql`
   - `supabase/migrations/0002_security_functions.sql`
   - `supabase/migrations/0003_admin_role.sql`

## Step 8: Seed the Admin User

```bash
railway run python scripts/seed_admin_user.py
```

## Step 9: Verify Deployment

Check the deployment logs:

```bash
railway logs
```

Test the health endpoint:

```bash
curl https://your-railway-domain.railway.app/health
```

## Required Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Supabase project URL | ✅ |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key | ✅ |
| `PAYSTACK_SECRET_KEY` | Paystack secret key | ✅ |
| `PAYSTACK_WEBHOOK_SECRET` | Paystack webhook secret | ✅ |
| `FRONTEND_URL` | Frontend URL for CORS | ✅ |
| `API_URL` | Backend public URL | ✅ |
| `RESEND_API_KEY` | Resend API key for emails | ✅ |
| `EMAIL_FROM` | Sender email address | ✅ |
| `EMAIL_FROM_NAME` | Sender name | ✅ |
| `DEFAULT_ADMIN_EMAIL` | Default admin email | ✅ |
| `DEFAULT_ADMIN_PASSWORD` | Default admin password | ✅ |
| `ENVIRONMENT` | Environment (production/development) | ✅ |

## Monitoring

View real-time logs:

```bash
railway logs --follow
```

## Scaling

Railway automatically scales based on demand. To manually scale:

```bash
railway scale --replicas 2
```

## Troubleshooting

### Common Issues

1. **Database connection errors**
   - Verify `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are correct
   - Check Supabase project is not paused

2. **Paystack webhook failures**
   - Verify `PAYSTACK_WEBHOOK_SECRET` matches the secret in Paystack dashboard
   - Ensure webhook URL is accessible from Paystack servers

3. **Email delivery failures**
   - Verify `RESEND_API_KEY` is valid
   - Check Resend dashboard for delivery status

4. **Admin login issues**
   - Run the seed script to create admin user
   - Verify `DEFAULT_ADMIN_EMAIL` and `DEFAULT_ADMIN_PASSWORD` are set

## Security Recommendations

1. Change `DEFAULT_ADMIN_PASSWORD` after first login
2. Use strong, unique API keys for production
3. Enable 2FA on your Railway and Supabase accounts
4. Regularly rotate API keys and secrets
5. Monitor audit logs for suspicious activity

## Support

For issues or questions:
- GitHub Issues: https://github.com/jemeokafor/surepay/issues
- Railway Documentation: https://docs.railway.app
- Supabase Documentation: https://supabase.com/docs