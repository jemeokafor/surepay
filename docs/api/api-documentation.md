# SurePay API Documentation

## Overview

The SurePay API provides endpoints for handling payment processing, webhook notifications, and payout management for the SurePay platform. This documentation covers all available endpoints, their parameters, responses, and authentication requirements.

## Base URL

```
https://your-deployment-url.up.railway.app
```

*Note: Replace with your actual deployment URL when deployed to Railway*

## Authentication

Most API endpoints are designed to be called by the frontend application and authenticated through Supabase. Webhook endpoints use signature verification for security.

## API Endpoints

### Health Check Endpoints

#### `GET /health`

Basic health check endpoint to verify the API is running.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "service": "SurePay Backend API"
}
```

#### `GET /health/supabase`

Check Supabase connection status.

**Response:**
```json
{
  "status": "healthy",
  "supabase": "connected"
}
```

#### `GET /health/paystack`

Check Paystack API connectivity.

**Response:**
```json
{
  "status": "healthy",
  "paystack": "connected"
}
```

#### `GET /health/all`

Comprehensive health check for all services.

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "supabase": "connected",
    "paystack": "connected"
  },
  "version": "1.0.0"
}
```

### Payment Endpoints

#### `POST /api/payments/initialize`

Initialize a new payment transaction.

**Request Body:**
```json
{
  "amount": 10000,
  "currency": "NGN",
  "vendor_id": "vendor-uuid",
  "product_id": "product-uuid",
  "customer_email": "customer@example.com",
  "metadata": {}
}
```

**Response:**
```json
{
  "status": "success",
  "transaction_id": "transaction-uuid",
  "authorization_url": "https://checkout.paystack.com/abc123"
}
```

#### `POST /api/payments/verify/{transaction_id}`

Verify payment status with Paystack.

**Path Parameters:**
- `transaction_id` (string): The transaction ID to verify

**Response:**
```json
{
  "status": true,
  "message": "Verification successful",
  "data": {
    "status": "success",
    "reference": "transaction-uuid",
    "amount": 10000
  }
}
```

### Payout Endpoints

#### `POST /api/payouts/create`

Create a new payout transfer.

**Request Body:**
```json
{
  "transaction_id": "transaction-uuid",
  "vendor_id": "vendor-uuid",
  "amount": 9500
}
```

**Response:**
```json
{
  "status": "success",
  "payout_id": "payout-uuid",
  "transfer_id": "transfer-id",
  "transfer_status": "pending"
}
```

#### `POST /api/payouts/retry/{transaction_id}`

Retry a failed payout.

**Path Parameters:**
- `transaction_id` (string): The transaction ID for the payout to retry

**Response:**
```json
{
  "status": "success",
  "transfer_id": "new-transfer-id",
  "transfer_status": "pending"
}
```

### Webhook Endpoints

#### `POST /api/webhooks/paystack`

Handle Paystack webhook events. This endpoint is called by Paystack to notify about payment and transfer events.

**Headers:**
- `x-paystack-signature`: HMAC signature for verification

**Request Body:**
```json
{
  "event": "charge.success",
  "data": {
    "reference": "transaction-uuid",
    "amount": 10000
  }
}
```

**Response:**
```json
{
  "status": "success"
}
```

## Webhook Events

The API handles the following Paystack webhook events:

### `charge.success`

Triggered when a payment is successfully completed. Updates the transaction status to `FUNDS_LOCKED`.

### `transfer.success`

Triggered when a payout transfer is successfully completed. Updates the payout status to `SUCCESS`.

### `transfer.failed`

Triggered when a payout transfer fails. Updates the payout status to `FAILED` with failure reason.

## Error Responses

All endpoints return appropriate HTTP status codes and error messages when operations fail.

**Common Error Response:**
```json
{
  "error": "Error description",
  "message": "Detailed error message"
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse. Excessive requests may result in 429 (Too Many Requests) responses.

## Security

- All webhook endpoints verify signatures using HMAC-SHA512
- HTTPS is required for all API calls
- Sensitive data is never logged
- Idempotency keys prevent duplicate operations

## Versioning

The API version is included in the documentation and health check responses. Breaking changes will result in a new major version.

## Support

For API support, contact the SurePay development team.