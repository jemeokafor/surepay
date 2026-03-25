# SurePay Developer Documentation

## Overview

This document provides technical information for developers working on or extending the SurePay application. It covers the architecture, code structure, development setup, and contribution guidelines.

## Architecture

### High-Level Architecture

SurePay follows a modern web application architecture:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend       │    │   Services      │
│   (Next.js)     │◄──►│   (FastAPI)      │◄──►│ (Paystack,      │
│                 │    │                  │    │  Supabase)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │    Database      │
                       │   (Supabase)     │
                       └──────────────────┘
```

### Technology Stack

**Frontend:**
- Next.js 16 (App Router)
- TypeScript
- Tailwind CSS
- React components
- Supabase client

**Backend:**
- FastAPI (Python)
- Uvicorn ASGI server
- Pydantic for data validation
- HTTPX for HTTP requests

**Database & Auth:**
- Supabase (PostgreSQL + Auth)
- Row-level security policies

**Payments:**
- Paystack API
- Webhook processing

**Infrastructure:**
- Vercel (Frontend deployment)
- Railway (Backend deployment)

## Project Structure

```
surepay/
├── backend/                 # FastAPI backend application
│   ├── app/                 # Main application code
│   │   ├── api/             # API route handlers
│   │   ├── core/            # Core configuration and utilities
│   │   ├── models/          # Data models
│   │   ├── services/        # Business logic and external services
│   │   └── main.py          # Application entry point
│   ├── tests/               # Test suite
│   ├── requirements.txt      # Python dependencies
│   ├── Dockerfile           # Container configuration
│   └── railway.toml          # Railway deployment config
├── frontend/                # Next.js frontend application
│   ├── src/                 # Source code
│   │   ├── app/             # App router pages
│   │   ├── components/      # React components
│   │   ├── lib/             # Utility functions
│   │   └── types/           # TypeScript types
│   └── public/              # Static assets
├── docs/                    # Documentation
├── site/                    # Static landing page
└── supabase/                # Database migrations
```

## Backend Development

### API Structure

The backend is organized into modules:

#### Core Module (`app/core/`)
- `config.py`: Application configuration using Pydantic Settings
- `security.py`: Security utilities including webhook signature verification

#### API Module (`app/api/`)
- `health.py`: Health check endpoints
- `payments.py`: Payment initialization and verification
- `payouts.py`: Payout creation and management
- `webhooks.py`: Webhook handling for external services

#### Services Module (`app/services/`)
- `paystack.py`: Paystack API client
- `supabase.py`: Supabase database client

### Running the Backend

1. **Set up the environment:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Configure environment variables:**
Create a `.env` file with your configuration:
```
SUPABASE_URL=your-supabase-url
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
PAYSTACK_SECRET_KEY=your-paystack-secret-key
PAYSTACK_WEBHOOK_SECRET=your-webhook-secret
FRONTEND_URL=http://localhost:3000
```

3. **Run the development server:**
```bash
source venv/bin/activate
python app/main.py
```

The API will be available at `http://localhost:8000`

### Testing

The backend includes a comprehensive test suite:

1. **Run all tests:**
```bash
cd backend
source venv/bin/activate
./run_tests.sh
```

2. **Run specific test categories:**
```bash
# Unit tests
python -m pytest tests/test_config.py tests/test_security.py

# API endpoint tests
python -m pytest tests/test_health.py tests/test_webhooks.py

# Service tests
python -m pytest tests/test_supabase_service.py tests/test_paystack_service.py
```

## Frontend Development

### Component Structure

The frontend follows a component-based architecture:

#### Pages (`src/app/`)
- `/` - Landing page
- `/dashboard` - Vendor dashboard
- `/products` - Product management
- `/payouts` - Payout history
- `/transactions` - Transaction history
- `/disputes` - Dispute management
- `/checkout/[id]` - Checkout flow
- `/login` - Authentication
- `/signup` - Registration

#### Components (`src/components/`)
- UI components (`src/components/ui/`)
- Dashboard components (`src/components/dashboard/`)
- Admin components (`src/components/admin/`)
- Checkout components (`src/components/checkout/`)

### Running the Frontend

1. **Install dependencies:**
```bash
cd frontend
npm install
```

2. **Run development server:**
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Environment Variables

Create a `.env.local` file in the frontend directory:
```
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_PAYSTACK_PUBLIC_KEY=your-paystack-public-key
```

## Database Schema

### Key Tables

#### `vendors`
Vendor information and payout details.

#### `products`
Vendor product listings (max 3 featured per vendor).

#### `transactions`
Payment transactions with state management.

#### `disputes`
Dispute records and resolution tracking.

#### `payouts`
Payout records and transfer status.

#### `vendor_public_metrics`
Aggregated trust metrics for public display.

### Row-Level Security

Supabase RLS ensures data isolation:
- Vendors can only access their own data
- Admin operations require backend service role
- Public metrics are read-only and derived

## Development Workflow

### Setting Up Development Environment

1. **Clone the repository:**
```bash
git clone https://github.com/jemeokafor/surepay.git
cd surepay
```

2. **Backend setup:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Frontend setup:**
```bash
cd frontend
npm install
```

4. **Database setup:**
- Create a Supabase project
- Apply migrations from `supabase/migrations/`
- Configure RLS policies

### Code Quality

#### Backend
- Follow PEP 8 style guide
- Use type hints for all functions
- Write docstrings for public functions
- Maintain test coverage above 80%

#### Frontend
- Use TypeScript for type safety
- Follow React best practices
- Maintain consistent component structure
- Write unit tests for complex components

### Testing

#### Backend Testing
- Unit tests for individual functions
- Integration tests for API endpoints
- Mock external services
- Test both success and failure cases

#### Frontend Testing
- Component rendering tests
- User interaction tests
- API integration tests
- End-to-end flow tests

### Deployment

#### Backend (Railway)
1. Create Railway account
2. Install Railway CLI
3. Run `railway init` in backend directory
4. Set environment variables in Railway dashboard
5. Run `railway up` to deploy

#### Frontend (Vercel)
1. Create Vercel account
2. Install Vercel CLI
3. Run `vercel` in frontend directory
4. Configure environment variables in Vercel dashboard
5. Run `vercel --prod` to deploy to production

## Contributing

### Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests for new functionality
5. Update documentation
6. Submit pull request

### Code Review Guidelines

- All code must be reviewed by at least one other developer
- Tests must pass before merging
- Documentation must be updated for new features
- Code must follow established patterns and style guides

### Issue Tracking

- Use GitHub Issues for bug reports and feature requests
- Label issues appropriately (bug, enhancement, documentation, etc.)
- Assign issues to team members
- Update issue status regularly

## Security

### Authentication

- Supabase Auth for user management
- Row-level security for data isolation
- JWT tokens for API authentication
- Session management with secure cookies

### Data Protection

- HTTPS encryption for all communications
- Environment variables for secrets
- Database encryption at rest
- Regular security audits

### Input Validation

- Server-side validation for all inputs
- Sanitization of user-provided data
- Rate limiting for API endpoints
- Protection against common web vulnerabilities

## Monitoring and Logging

### Backend Logging

- Structured logging with timestamps
- Error logging with stack traces
- Performance monitoring
- Audit trails for sensitive operations

### Frontend Monitoring

- Error boundaries for React components
- Performance monitoring with Web Vitals
- User interaction tracking
- Analytics for feature usage

## Performance Optimization

### Backend

- Database connection pooling
- Caching for frequently accessed data
- Asynchronous processing for non-critical operations
- Efficient database queries with proper indexing

### Frontend

- Code splitting for faster initial loads
- Image optimization
- Lazy loading for non-critical components
- Bundle size optimization

## Troubleshooting

### Common Development Issues

#### Database Connection Errors
- Verify Supabase credentials
- Check network connectivity
- Ensure RLS policies are correct

#### Authentication Issues
- Verify environment variables
- Check Supabase Auth configuration
- Review session management

#### Payment Processing Errors
- Verify Paystack API keys
- Check webhook configuration
- Review signature verification

### Debugging Tips

#### Backend Debugging
- Use logging statements for tracing
- Enable debug mode for detailed output
- Check Railway logs for deployment issues
- Use local development server for testing

#### Frontend Debugging
- Use browser developer tools
- Check network tab for API calls
- Review console for JavaScript errors
- Use React DevTools for component inspection

## API Reference

See `docs/api/api-documentation.md` for detailed API endpoint documentation.

## Testing Reference

See `docs/test-suite.md` for comprehensive testing documentation.

## Deployment Reference

See `docs/backend-deployment.md` and `docs/railway-deployment-guide.md` for deployment documentation.