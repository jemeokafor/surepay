# SurePay Deployment Guide

## Overview

This guide provides detailed instructions for deploying the SurePay application to production environments. It covers both frontend and backend deployment processes.

## Prerequisites

### Accounts and Services

1. **GitHub Account** - For version control
2. **Railway Account** - For backend deployment
3. **Vercel Account** - For frontend deployment
4. **Supabase Account** - For database and authentication
5. **Paystack Account** - For payment processing

### Local Development Environment

1. **Node.js** (v18 or higher)
2. **Python** (v3.11 or higher)
3. **Git**
4. **Railway CLI**
5. **Vercel CLI**

## Backend Deployment (Railway)

### Step 1: Prepare Supabase

1. **Create Supabase Project**
   - Go to https://supabase.com
   - Create a new project
   - Note the Project URL and API keys

2. **Configure Supabase Settings**
   - In Supabase Dashboard → Settings → API
   - Copy Project URL and `service_role` key

3. **Set up Database Schema**
   - Apply migrations from `supabase/migrations/`
   - Configure Row-Level Security (RLS) policies

### Step 2: Configure Paystack

1. **Get API Keys**
   - Go to Paystack Dashboard → Settings → API Keys & Webhooks
   - Copy Secret Key and create a Webhook Secret

2. **Configure Webhooks**
   - Add webhook URL: `https://your-backend-url.up.railway.app/api/webhooks/paystack`
   - Select events: `charge.success`, `transfer.success`, `transfer.failed`

### Step 3: Deploy to Railway

1. **Install Railway CLI**
```bash
npm install -g @railway/cli
```

2. **Login to Railway**
```bash
railway login
```

3. **Initialize Railway Project**
```bash
cd backend
railway init
```

4. **Set Environment Variables**
In Railway Dashboard → Variables, set:
```
SUPABASE_URL=your-supabase-project-url
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
PAYSTACK_SECRET_KEY=your-paystack-secret-key
PAYSTACK_WEBHOOK_SECRET=your-webhook-secret
FRONTEND_URL=https://your-frontend-url.vercel.app
```

5. **Deploy**
```bash
railway up
```

### Step 4: Verify Deployment

1. **Check Health Endpoints**
   - `https://your-backend-url.up.railway.app/health`
   - `https://your-backend-url.up.railway.app/health/supabase`
   - `https://your-backend-url.up.railway.app/health/paystack`

2. **Test Webhooks**
   - Send test webhook from Paystack Dashboard
   - Check Railway logs for successful processing

## Frontend Deployment (Vercel)

### Step 1: Prepare Environment Variables

Create environment variables for your frontend:

```
NEXT_PUBLIC_SUPABASE_URL=your-supabase-project-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
NEXT_PUBLIC_PAYSTACK_PUBLIC_KEY=your-paystack-public-key
NEXT_PUBLIC_APP_URL=https://your-frontend-url.vercel.app
```

### Step 2: Deploy to Vercel

1. **Install Vercel CLI**
```bash
npm install -g vercel
```

2. **Login to Vercel**
```bash
vercel login
```

3. **Deploy Project**
```bash
cd frontend
vercel
```

4. **Configure Environment Variables**
In Vercel Dashboard → Settings → Environment Variables, add the variables from Step 1.

5. **Deploy to Production**
```bash
vercel --prod
```

### Step 3: Verify Deployment

1. **Check Landing Page**
   - Visit your frontend URL
   - Verify landing page loads correctly

2. **Test Authentication**
   - Try signing up and logging in
   - Verify Google OAuth works

3. **Test Payment Flow**
   - Create a test transaction
   - Verify checkout flow works

## Database Setup

### Supabase Configuration

1. **Apply Migrations**
```bash
cd supabase
supabase link --project-ref your-project-ref
supabase db push
```

2. **Configure Auth**
   - Enable Email and Google authentication
   - Configure email templates
   - Set up email confirmation

3. **Set up Storage**
   - Create buckets for evidence files
   - Configure access policies

4. **Configure RLS Policies**
   - Apply row-level security to all tables
   - Test policies with different user roles

## Environment Variables Summary

### Backend (Railway)
| Variable | Description | Required |
|----------|-------------|----------|
| SUPABASE_URL | Supabase project URL | Yes |
| SUPABASE_SERVICE_ROLE_KEY | Supabase service role key | Yes |
| PAYSTACK_SECRET_KEY | Paystack secret key | Yes |
| PAYSTACK_WEBHOOK_SECRET | Paystack webhook secret | Yes |
| FRONTEND_URL | Frontend URL for CORS | Yes |

### Frontend (Vercel)
| Variable | Description | Required |
|----------|-------------|----------|
| NEXT_PUBLIC_SUPABASE_URL | Supabase project URL | Yes |
| NEXT_PUBLIC_SUPABASE_ANON_KEY | Supabase anonymous key | Yes |
| NEXT_PUBLIC_PAYSTACK_PUBLIC_KEY | Paystack public key | Yes |
| NEXT_PUBLIC_APP_URL | Application URL | Yes |

## Monitoring and Maintenance

### Health Checks

Regularly monitor these endpoints:
- `/health` - Basic health check
- `/health/supabase` - Database connectivity
- `/health/paystack` - Payment service connectivity

### Logging

Set up logging for:
- Error tracking with Sentry or similar
- Performance monitoring
- Business metrics tracking

### Backup Strategy

1. **Database Backups**
   - Enable Supabase automatic backups
   - Regular manual backups for critical data

2. **Code Backups**
   - Push to GitHub regularly
   - Tag releases for rollback capability

### Scaling Considerations

1. **Database Scaling**
   - Monitor connection limits
   - Upgrade Supabase plan as needed

2. **API Scaling**
   - Railway automatically scales based on demand
   - Monitor response times and error rates

3. **Frontend Scaling**
   - Vercel provides automatic scaling
   - Optimize bundle sizes for performance

## Troubleshooting

### Common Deployment Issues

#### Backend Deployment Failures
- **Missing Environment Variables**: Ensure all required variables are set
- **Database Connection**: Verify Supabase credentials and network access
- **Dependency Issues**: Check `requirements.txt` and Python version compatibility

#### Frontend Deployment Failures
- **Build Errors**: Check for TypeScript/JavaScript errors
- **Environment Variables**: Verify all required variables are configured
- **Routing Issues**: Check Next.js configuration and routing setup

#### Payment Processing Issues
- **Webhook Verification**: Check webhook secret and signature verification
- **Paystack API Errors**: Verify API keys and account status
- **Payout Failures**: Check bank account details and Paystack recipient setup

### Recovery Procedures

1. **Rollback Process**
   - Use Git tags for version control
   - Deploy previous working version
   - Update environment variables if needed

2. **Database Recovery**
   - Use Supabase backup restore
   - Contact Supabase support for assistance

3. **Service Outages**
   - Monitor status pages for third-party services
   - Implement fallback mechanisms where possible
   - Communicate with users about service status

## Security Considerations

### Production Security

1. **Environment Variables**
   - Never commit secrets to version control
   - Use secret management tools
   - Rotate credentials regularly

2. **Network Security**
   - Use HTTPS for all communications
   - Configure proper CORS settings
   - Implement rate limiting

3. **Data Security**
   - Encrypt sensitive data at rest
   - Use parameterized queries to prevent SQL injection
   - Implement proper input validation

### Compliance

1. **Data Privacy**
   - Comply with applicable data protection laws
   - Implement data retention policies
   - Provide data export and deletion capabilities

2. **Payment Security**
   - Follow PCI DSS compliance requirements
   - Use tokenization for sensitive data
   - Implement fraud detection measures

## Performance Optimization

### Backend Optimization

1. **Database Optimization**
   - Add indexes for frequently queried columns
   - Optimize query performance
   - Use connection pooling

2. **Caching Strategy**
   - Implement Redis or similar caching
   - Cache frequently accessed data
   - Set appropriate cache expiration

### Frontend Optimization

1. **Bundle Optimization**
   - Minimize JavaScript bundle size
   - Use code splitting
   - Optimize images and assets

2. **Performance Monitoring**
   - Monitor Core Web Vitals
   - Track page load times
   - Optimize for mobile performance

## Updates and Maintenance

### Regular Maintenance Tasks

1. **Dependency Updates**
   - Regularly update backend dependencies
   - Update frontend packages
   - Test for breaking changes

2. **Security Updates**
   - Monitor for security vulnerabilities
   - Apply security patches promptly
   - Conduct regular security audits

3. **Performance Reviews**
   - Monitor application performance
   - Optimize slow queries
   - Review and improve user experience

### Version Management

1. **Git Workflow**
   - Use feature branches for development
   - Tag releases for easy rollback
   - Maintain a changelog

2. **Deployment Strategy**
   - Use staging environment for testing
   - Implement blue-green deployment for zero downtime
   - Monitor deployments for issues

## Support and Resources

### Documentation

- API Documentation: `docs/api/api-documentation.md`
- User Guide: `docs/user-guide.md`
- Developer Documentation: `docs/developer-documentation.md`
- Test Suite Documentation: `docs/test-suite.md`

### Contact Support

For deployment assistance:
- GitHub Issues: https://github.com/jemeokafor/surepay/issues
- Email: support@surepay.link
- Community: Discord/Slack channels

## Conclusion

This deployment guide provides a comprehensive approach to deploying SurePay to production. By following these steps and maintaining proper monitoring and maintenance procedures, you can ensure a reliable and secure deployment of the SurePay platform.