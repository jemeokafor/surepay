# SurePay Supabase Setup Guide

This guide walks you through setting up the Supabase database for SurePay MVP.

## Prerequisites

1. Supabase account (free tier sufficient for MVP)
2. Supabase CLI installed locally
3. PostgreSQL client (optional, for manual queries)

## Step 1: Create Supabase Project

```bash
# Via web interface
1. Go to https://supabase.com/dashboard
2. Click "New Project"
3. Name: "surepay-mvp"
4. Region: Choose closest to Nigeria (Europe West recommended)
5. Database password: Generate strong password
```

## Step 2: Get Connection Credentials

From your Supabase project dashboard:

1. Go to **Project Settings** → **API**
2. Copy these values:
   - **Project URL** (NEXT_PUBLIC_SUPABASE_URL)
   - **anon public** key (NEXT_PUBLIC_SUPABASE_ANON_KEY)
   - **service_role secret** key (SUPABASE_SERVICE_ROLE_KEY) ⚠️ Keep secure!

## Step 3: Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and fill in your Supabase credentials
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

## Step 4: Apply Database Migrations

### Option A: Using Supabase Dashboard (Recommended for Quick Start)

1. Go to **SQL Editor** in your Supabase dashboard
2. Open `supabase/migrations/0001_surepay_initial_schema.sql`
3. Copy contents and paste into SQL Editor
4. Click **Run**
5. Repeat for `0002_security_functions.sql`

### Option B: Using Supabase CLI

```bash
# Install Supabase CLI if not already installed
npm install -g supabase

# Login to Supabase
supabase login

# Link to your project
supabase link --project-ref your-project-ref

# Apply migrations
supabase db push
```

## Step 5: Configure Authentication

1. Go to **Authentication** → **Providers**
2. Enable these providers:
   - **Email** (Magic Link)
   - **Google OAuth** (optional, for faster onboarding)

3. Configure Email settings:
   - Go to **Authentication** → **Email Templates**
   - Customize Magic Link template:
     ```
     <h2>Magic Link</h2>
     <p>Click the button below to sign in to SurePay:</p>
     <a href="{{ .ConfirmationURL }}">Sign In</a>
     ```

## Step 6: Configure Storage (Optional)

For evidence uploads:

1. Go to **Storage** → **New Bucket**
2. Create bucket: `dispute-evidence`
3. Set **Public** to false (private)
4. Configure CORS if needed

## Step 7: Verify Setup

Run these queries in the SQL Editor to verify:

```sql
-- Check tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';

-- Expected tables:
-- vendors, products, transactions, payouts, disputes, 
-- transaction_events, notification_logs, vendor_public_metrics

-- Check RLS is enabled
SELECT relname, relrowsecurity 
FROM pg_class 
WHERE relname IN ('vendors', 'transactions', 'products');

-- Should show "t" (true) for relrowsecurity

-- Test vendor creation (will auto-create from auth trigger)
SELECT * FROM vendors LIMIT 1;
```

## Step 8: Set Up Paystack Webhook

1. Get your webhook endpoint:
   ```
   https://your-project.supabase.co/functions/v1/paystack-webhook
   ```

2. In Paystack Dashboard:
   - Go to **Settings** → **Webhooks**
   - Add endpoint URL
   - Set secret key (save in supabase secrets)

3. Store webhook secret in Supabase:
   ```bash
   supabase secrets set PAYSTACK_WEBHOOK_SECRET=your_webhook_secret
   ```

## Step 9: Configure Edge Functions (Optional)

For serverless webhooks and cron jobs:

```bash
# Deploy edge function
supabase functions deploy paystack-webhook

# Set secrets
supabase secrets set PAYSTACK_SECRET_KEY=sk_test_...
supabase secrets set WEBHOOK_SECRET=whsec_...
```

## Step 10: Database Backups

Supabase automatically backs up your database. To download a backup:

1. Go to **Database** → **Backups**
2. Click **Download** on the desired backup

Or use CLI:
```bash
supabase db dump -f backup.sql
```

## Troubleshooting

### Issue: RLS policies blocking queries

**Solution:** Ensure you're using the service_role key for backend operations, or anon key with proper JWT for frontend.

### Issue: Webhook signature verification fails

**Solution:** 
1. Verify PAYSTACK_WEBHOOK_SECRET is set correctly
2. Check payload is not modified before verification
3. Ensure timestamps are within acceptable range (5 min)

### Issue: Auto-release cron job not working

**Solution:**
1. Verify `pg_cron` extension is enabled
2. Check cron job is scheduled: `SELECT * FROM cron.job;`
3. Review logs: `SELECT * FROM cron.job_run_details;`

### Issue: Duplicate transactions from webhooks

**Solution:** 
The idempotency logic should prevent this. Check:
1. `paystack_reference` is unique in transactions table
2. Webhook handler checks for existing transactions first
3. Using `SELECT ... FOR UPDATE` for critical operations

## Security Checklist

- [ ] RLS policies enabled on all tables
- [ ] service_role key never exposed to frontend
- [ ] Webhook signatures verified
- [ ] Rate limiting on sensitive endpoints
- [ ] Evidence uploads restricted by size/type
- [ ] Admin functions use SECURITY DEFINER
- [ ] JWT tokens have appropriate expiry
- [ ] Database passwords rotated regularly

## Performance Optimization

The schema includes these optimizations:

1. **Indexes:** All foreign keys and frequently queried columns
2. **Auto-release index:** `idx_transactions_auto_release` for cron efficiency
3. **Partial indexes:** Featured products, active vendors
4. **Materialized view:** vendor_public_metrics for trust badges

Monitor query performance:
```sql
-- Check for slow queries
SELECT query, calls, mean_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

## Next Steps

1. Connect your Next.js frontend to Supabase
2. Set up FastAPI backend for business logic
3. Configure Paystack integration
4. Test the full payment flow
5. Set up monitoring (Sentry)

## Support

- Supabase Docs: https://supabase.com/docs
- PostgreSQL Docs: https://www.postgresql.org/docs/
- SurePay BRD: See `docs/03-product-brd-v2.1.md`
- Architecture Guide: See `docs/01-architecture-and-regulation.md`
