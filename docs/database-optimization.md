# Database Optimization Module for SurePay

## Overview

This module provides database optimization features including indexing strategies,
query optimization, and performance monitoring for the SurePay application.

## Indexing Strategies

### Transactions Table Indexes

1. **Primary Index**: `id` (Primary Key)
2. **Status Index**: `status` for filtering by transaction state
3. **Vendor Index**: `vendor_id` for vendor-specific queries
4. **Date Index**: `created_at` for time-based queries
5. **Payment Status Index**: `payment_status` for payment filtering
6. **Composite Index**: `(vendor_id, status)` for vendor dashboard queries

### Vendors Table Indexes

1. **Primary Index**: `id` (Primary Key)
2. **Username Index**: `username` for public profile lookups
3. **Status Index**: `status` for active vendor filtering
4. **Payout Ready Index**: `payout_ready` for onboarding status
5. **Created Date Index**: `created_at` for analytics

### Payouts Table Indexes

1. **Primary Index**: `id` (Primary Key)
2. **Transaction Index**: `transaction_id` for transaction lookups
3. **Vendor Index**: `vendor_id` for vendor-specific queries
4. **Status Index**: `status` for payout status filtering
5. **Date Index**: `created_at` for time-based queries
6. **Composite Index**: `(vendor_id, status)` for vendor payout queries

### Disputes Table Indexes

1. **Primary Index**: `id` (Primary Key)
2. **Transaction Index**: `transaction_id` for transaction lookups
3. **Status Index**: `status` for dispute status filtering
4. **Date Index**: `opened_at` for time-based queries
5. **Composite Index**: `(status, opened_at)` for dispute queue queries

## Query Optimization Techniques

### 1. Pagination
- Use `LIMIT` and `OFFSET` for large result sets
- Implement cursor-based pagination for better performance
- Avoid `OFFSET` with large numbers

### 2. Selective Column Retrieval
- Only select required columns
- Use `SELECT specific_columns` instead of `SELECT *`
- Avoid large JSON fields in list queries

### 3. Efficient Joins
- Use appropriate join types
- Ensure join conditions use indexed columns
- Limit joined table sizes

### 4. Query Caching
- Cache frequently accessed data
- Use appropriate TTL values
- Invalidate cache on data changes

## Performance Monitoring

### Key Metrics to Monitor

1. **Query Response Time**: Average and 95th percentile
2. **Database Connections**: Active and idle connections
3. **Index Usage**: Hit rate and effectiveness
4. **Cache Hit Rate**: Memory and Redis cache performance
5. **Slow Query Log**: Queries taking longer than threshold

### Supabase-Specific Optimizations

1. **RLS Performance**: Optimize row-level security policies
2. **Realtime Subscriptions**: Efficient channel management
3. **Storage Performance**: Optimize file access patterns
4. **Function Performance**: Serverless function optimization

## Implementation Recommendations

### 1. Create Indexes in Supabase

```sql
-- Transactions table indexes
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_vendor ON transactions(vendor_id);
CREATE INDEX idx_transactions_created ON transactions(created_at);
CREATE INDEX idx_transactions_payment_status ON transactions(payment_status);
CREATE INDEX idx_transactions_vendor_status ON transactions(vendor_id, status);

-- Vendors table indexes
CREATE INDEX idx_vendors_username ON vendors(username);
CREATE INDEX idx_vendors_status ON vendors(status);
CREATE INDEX idx_vendors_payout_ready ON vendors(payout_ready);
CREATE INDEX idx_vendors_created ON vendors(created_at);

-- Payouts table indexes
CREATE INDEX idx_payouts_transaction ON payouts(transaction_id);
CREATE INDEX idx_payouts_vendor ON payouts(vendor_id);
CREATE INDEX idx_payouts_status ON payouts(status);
CREATE INDEX idx_payouts_created ON payouts(created_at);
CREATE INDEX idx_payouts_vendor_status ON payouts(vendor_id, status);

-- Disputes table indexes
CREATE INDEX idx_disputes_transaction ON disputes(transaction_id);
CREATE INDEX idx_disputes_status ON disputes(status);
CREATE INDEX idx_disputes_opened ON disputes(opened_at);
CREATE INDEX idx_disputes_status_opened ON disputes(status, opened_at);
```

### 2. Query Optimization Examples

```sql
-- Efficient transaction query for vendor dashboard
SELECT id, product_name, amount_ngn, status, created_at 
FROM transactions 
WHERE vendor_id = $1 
  AND status IN ('FUNDS_LOCKED', 'AWAITING_BUYER_CONFIRMATION', 'RELEASED')
ORDER BY created_at DESC 
LIMIT 20;

-- Efficient payout query for vendor history
SELECT id, amount_ngn, status, initiated_at, succeeded_at, failed_at
FROM payouts 
WHERE vendor_id = $1 
ORDER BY created_at DESC 
LIMIT 50;

-- Efficient dispute query for admin console
SELECT d.id, d.reason_code, d.status, d.opened_at,
       t.amount_ngn, t.product_name, v.display_name
FROM disputes d
JOIN transactions t ON d.transaction_id = t.id
JOIN vendors v ON t.vendor_id = v.id
WHERE d.status = 'open'
ORDER BY d.opened_at ASC
LIMIT 30;
```

## Monitoring and Alerting

### Performance Thresholds

1. **Query Response Time**: > 100ms should be investigated
2. **Database Connections**: > 80% of limit should trigger alerts
3. **Cache Hit Rate**: < 90% indicates caching issues
4. **Slow Queries**: > 500ms should be logged and analyzed

### Supabase Monitoring

1. **Project Metrics**: Monitor in Supabase Dashboard
2. **Database Logs**: Enable and review PostgreSQL logs
3. **Realtime Metrics**: Monitor WebSocket connections
4. **Storage Metrics**: Track file access patterns

## Best Practices

### 1. Index Management
- Regularly review index usage statistics
- Remove unused indexes to reduce write overhead
- Add indexes based on query patterns
- Monitor index size and performance impact

### 2. Query Optimization
- Use `EXPLAIN ANALYZE` to analyze query plans
- Avoid functions in WHERE clauses
- Use appropriate data types
- Normalize vs. denormalize based on access patterns

### 3. Connection Management
- Use connection pooling
- Close connections properly
- Monitor connection leaks
- Optimize connection timeouts

### 4. Data Archiving
- Archive old transaction data
- Implement data retention policies
- Use partitioning for large tables
- Monitor storage growth

## Future Enhancements

### 1. Advanced Indexing
- Partial indexes for specific conditions
- Expression indexes for computed values
- Multicolumn indexes for complex queries
- Covering indexes for index-only scans

### 2. Query Plan Optimization
- Materialized views for complex aggregations
- Query plan caching
- Statistics updates for better planning
- Partition pruning for large datasets

### 3. Performance Testing
- Load testing with realistic data volumes
- Stress testing for peak usage scenarios
- Regression testing for performance changes
- Automated performance benchmarking

This optimization guide provides a comprehensive approach to database performance
for the SurePay application, ensuring efficient data access and scalability.