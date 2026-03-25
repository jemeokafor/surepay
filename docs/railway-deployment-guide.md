# Railway Deployment Guide for SurePay Backend

## Prerequisites

1. Railway account (https://railway.com)
2. Supabase project with credentials
3. Paystack account with API keys

## Deployment Steps

### 1. Create Supabase Project

1. Go to https://supabase.com and create a new project
2. Get your project URL and service role key from Settings > API

### 2. Get Paystack API Keys

1. Go to https://dashboard.paystack.com
2. Navigate to Settings > API Keys & Webhooks
3. Copy your Secret Key and create a Webhook Secret

### 3. Deploy to Railway

1. Install Railway CLI:
   ```bash
   npm install -g @railway/cli
   ```

2. Login to Railway:
   ```bash
   railway login
   ```

3. Initialize Railway project:
   ```bash
   cd backend
   railway init
   ```

4. Set environment variables in Railway dashboard:
   - `SUPABASE_URL` - Your Supabase project URL
   - `SUPABASE_SERVICE_ROLE_KEY` - Your Supabase service role key
   - `PAYSTACK_SECRET_KEY` - Your Paystack secret key
   - `PAYSTACK_WEBHOOK_SECRET` - Your Paystack webhook secret
   - `FRONTEND_URL` - Your frontend URL (e.g., https://your-app.vercel.app)

5. Deploy:
   ```bash
   railway up
   ```

### 4. Configure Paystack Webhooks

1. In Paystack dashboard, go to Settings > API Keys & Webhooks
2. Add a new webhook with URL: `https://your-railway-app.up.railway.app/api/webhooks/paystack`
3. Set the webhook secret in Railway environment variables

### 5. Verify Deployment

1. Check Railway logs for successful deployment
2. Test health endpoint: `https://your-railway-app.up.railway.app/health`
3. Test API endpoints with sample requests

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| SUPABASE_URL | Supabase project URL | Yes |
| SUPABASE_SERVICE_ROLE_KEY | Supabase service role key | Yes |
| PAYSTACK_SECRET_KEY | Paystack secret key | Yes |
| PAYSTACK_WEBHOOK_SECRET | Paystack webhook secret | Yes |
| FRONTEND_URL | Frontend URL for CORS | Yes |

## Troubleshooting

### Common Issues

1. **Supabase connection failed**: Check credentials and network connectivity
2. **Paystack webhooks not working**: Verify webhook URL and secret
3. **CORS errors**: Check FRONTEND_URL environment variable
4. **Deployment fails**: Check Railway logs for specific error messages

### Health Checks

Monitor these endpoints:
- `/health` - Basic health check
- `/health/supabase` - Supabase connectivity
- `/health/paystack` - Paystack API connectivity