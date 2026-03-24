-- SurePay MVP Database Schema
-- Version: 1.0.0
-- Date: March 24, 2026
-- Based on BRD v2.1 and Architecture & Regulation documents

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================
-- ENUM TYPES
-- ============================================

-- Transaction status states per BRD Section 9
CREATE TYPE transaction_status AS ENUM (
    'PENDING_PAYMENT',
    'FUNDS_LOCKED',
    'AWAITING_BUYER_CONFIRMATION',
    'DISPUTED',
    'RELEASED',
    'REFUNDED',
    'EXPIRED',
    'CANCELLED'
);

-- Payment status for tracking Paystack states
CREATE TYPE payment_status AS ENUM (
    'INITIATED',
    'PENDING',
    'SUCCESS',
    'FAILED',
    'REFUNDED'
);

-- Payout status for transfer tracking
CREATE TYPE payout_status AS ENUM (
    'queued',
    'processing',
    'succeeded',
    'failed',
    'reversed'
);

-- Dispute status and reason codes
CREATE TYPE dispute_status AS ENUM (
    'open',
    'under_review',
    'resolved_release',
    'resolved_refund',
    'cancelled'
);

CREATE TYPE dispute_reason AS ENUM (
    'non_delivery',
    'wrong_item',
    'damaged_item',
    'counterfeit',
    'not_as_described',
    'other'
);

-- Vendor status for account management
CREATE TYPE vendor_status AS ENUM (
    'active',
    'restricted',
    'suspended'
);

-- Actor types for audit logging
CREATE TYPE actor_type AS ENUM (
    'buyer',
    'vendor',
    'admin',
    'system',
    'webhook'
);

-- Notification channels
CREATE TYPE notification_channel AS ENUM (
    'email',
    'sms',
    'whatsapp'
);

-- Transaction source
CREATE TYPE transaction_source AS ENUM (
    'custom_link',
    'storefront'
);

-- ============================================
-- CORE TABLES
-- ============================================

-- Vendors table (extends Supabase Auth users)
-- Per BRD Section 17
CREATE TABLE vendors (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    brand_bio TEXT,
    avatar_url TEXT,
    
    -- Banking details (required for payouts)
    bank_code TEXT,
    account_number TEXT,
    account_name TEXT,
    recipient_code TEXT, -- Paystack transfer recipient
    payout_ready BOOLEAN DEFAULT false,
    
    -- Trust badge settings
    trust_badge_enabled BOOLEAN DEFAULT true,
    status vendor_status DEFAULT 'active',
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT username_format CHECK (username ~ '^[a-zA-Z0-9_]+$'),
    CONSTRAINT username_length CHECK (LENGTH(username) >= 3 AND LENGTH(username) <= 30)
);

-- Products table
-- Per BRD Section 17
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vendor_id UUID NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    image_url TEXT,
    price_ngn INTEGER NOT NULL CHECK (price_ngn > 0),
    is_featured BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Business rule: max 3 featured items per vendor
    CONSTRAINT featured_limit CHECK (
        NOT is_featured OR (
            SELECT COUNT(*) FROM products p 
            WHERE p.vendor_id = products.vendor_id 
            AND p.is_featured = true 
            AND p.id != products.id
        ) < 3
    )
);

-- Transactions table
-- Per BRD Section 17 - State Machine per BRD Section 9
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vendor_id UUID NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id) ON DELETE SET NULL,
    source transaction_source NOT NULL,
    
    -- Product snapshot at time of transaction
    product_name TEXT NOT NULL,
    product_snapshot JSONB NOT NULL,
    
    -- Buyer information
    buyer_name TEXT,
    buyer_email TEXT NOT NULL,
    buyer_whatsapp TEXT,
    
    -- Financial details
    amount_ngn INTEGER NOT NULL CHECK (amount_ngn > 0),
    fee_ngn INTEGER NOT NULL CHECK (fee_ngn >= 0),
    vendor_net_ngn INTEGER NOT NULL CHECK (vendor_net_ngn >= 0),
    currency TEXT DEFAULT 'NGN',
    
    -- Status tracking
    status transaction_status DEFAULT 'PENDING_PAYMENT',
    payment_status payment_status DEFAULT 'INITIATED',
    
    -- Paystack integration
    paystack_reference TEXT UNIQUE,
    paystack_access_code TEXT,
    
    -- Security
    buyer_access_token_hash TEXT,
    
    -- Timing
    expires_at TIMESTAMPTZ,
    paid_at TIMESTAMPTZ,
    delivery_marked_at TIMESTAMPTZ,
    auto_release_at TIMESTAMPTZ, -- 24h timer per BRD Section 11
    released_at TIMESTAMPTZ,
    refunded_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Risk cap: NGN 250,000 default per BRD Section 13
    CONSTRAINT max_amount CHECK (amount_ngn <= 250000)
);

-- Payouts table
-- Per BRD Section 17
CREATE TABLE payouts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_id UUID UNIQUE NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
    vendor_id UUID NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
    
    -- Transfer details
    amount_ngn INTEGER NOT NULL CHECK (amount_ngn > 0),
    recipient_code TEXT NOT NULL,
    transfer_reference TEXT UNIQUE,
    
    -- Status tracking
    status payout_status DEFAULT 'queued',
    failure_reason TEXT,
    attempt_count INTEGER DEFAULT 0,
    
    -- Timing
    initiated_at TIMESTAMPTZ,
    succeeded_at TIMESTAMPTZ,
    failed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Disputes table
-- Per BRD Section 17
CREATE TABLE disputes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_id UUID UNIQUE NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
    opened_by actor_type NOT NULL,
    reason_code dispute_reason NOT NULL,
    description TEXT,
    
    -- Evidence storage (JSONB for flexibility)
    buyer_evidence JSONB DEFAULT '{}',
    vendor_evidence JSONB DEFAULT '{}',
    
    -- Resolution
    status dispute_status DEFAULT 'open',
    resolution_notes TEXT,
    resolved_by UUID REFERENCES auth.users(id),
    
    -- Timing
    opened_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Transaction Events (Immutable audit log)
-- Per BRD Section 17
CREATE TABLE transaction_events (
    id BIGSERIAL PRIMARY KEY,
    transaction_id UUID NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
    actor_type actor_type NOT NULL,
    actor_id UUID,
    event_type TEXT NOT NULL, -- 'payment_received', 'delivery_marked', etc.
    payload JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Notification Logs
-- Per BRD Section 17
CREATE TABLE notification_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_id UUID REFERENCES transactions(id) ON DELETE CASCADE,
    recipient_type actor_type NOT NULL,
    channel notification_channel NOT NULL,
    template_key TEXT NOT NULL,
    status TEXT DEFAULT 'queued',
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    sent_at TIMESTAMPTZ
);

-- Vendor Public Metrics (Denormalized trust scores)
-- Per BRD Section 17
CREATE TABLE vendor_public_metrics (
    vendor_id UUID PRIMARY KEY REFERENCES vendors(id) ON DELETE CASCADE,
    protected_sales_count INTEGER DEFAULT 0,
    released_volume_ngn BIGINT DEFAULT 0,
    successful_payouts_count INTEGER DEFAULT 0,
    resolved_disputes_count INTEGER DEFAULT 0,
    buyer_favor_resolutions_count INTEGER DEFAULT 0,
    vendor_favor_resolutions_count INTEGER DEFAULT 0,
    last_completed_settlement_at TIMESTAMPTZ,
    last_successful_payout_at TIMESTAMPTZ,
    trust_score_version TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================
-- Per Supabase Best Practices: Critical indexes for query performance

-- Vendors indexes
CREATE INDEX idx_vendors_username ON vendors(username);
CREATE INDEX idx_vendors_status ON vendors(status);
CREATE INDEX idx_vendors_payout_ready ON vendors(payout_ready) WHERE payout_ready = true;

-- Products indexes
CREATE INDEX idx_products_vendor ON products(vendor_id);
CREATE INDEX idx_products_featured ON products(vendor_id, is_featured) WHERE is_featured = true;
CREATE INDEX idx_products_active ON products(vendor_id, is_active) WHERE is_active = true;

-- Transactions indexes (critical for performance)
CREATE INDEX idx_transactions_vendor ON transactions(vendor_id);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_paystack_ref ON transactions(paystack_reference);
CREATE INDEX idx_transactions_buyer_email ON transactions(buyer_email);

-- Critical: Index for auto-release cron job per BRD Section 11
CREATE INDEX idx_transactions_auto_release 
    ON transactions(status, auto_release_at) 
    WHERE status = 'AWAITING_BUYER_CONFIRMATION';

-- Index for webhook idempotency checks
CREATE INDEX idx_transactions_paystack_ref_status 
    ON transactions(paystack_reference, status);

-- Payouts indexes
CREATE INDEX idx_payouts_vendor ON payouts(vendor_id);
CREATE INDEX idx_payouts_status ON payouts(status);
CREATE INDEX idx_payouts_transaction ON payouts(transaction_id);

-- Disputes indexes
CREATE INDEX idx_disputes_transaction ON disputes(transaction_id);
CREATE INDEX idx_disputes_status ON disputes(status);
CREATE INDEX idx_disputes_opened_by ON disputes(opened_by);

-- Events indexes
CREATE INDEX idx_events_transaction ON transaction_events(transaction_id);
CREATE INDEX idx_events_type ON transaction_events(event_type);
CREATE INDEX idx_events_created ON transaction_events(created_at);

-- Notification indexes
CREATE INDEX idx_notifications_transaction ON notification_logs(transaction_id);
CREATE INDEX idx_notifications_status ON notification_logs(status);

-- ============================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================
-- Per BRD Section 18: Vendors see only their data

-- Enable RLS on all tables
ALTER TABLE vendors ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE payouts ENABLE ROW LEVEL SECURITY;
ALTER TABLE disputes ENABLE ROW LEVEL SECURITY;
ALTER TABLE transaction_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE vendor_public_metrics ENABLE ROW LEVEL SECURITY;

-- Vendors: Users can only see their own data
CREATE POLICY "Vendors can view own data" 
    ON vendors FOR SELECT 
    USING (auth.uid() = id);

CREATE POLICY "Vendors can update own data" 
    ON vendors FOR UPDATE 
    USING (auth.uid() = id);

-- Products: Vendors can manage their own products
CREATE POLICY "Vendors can view own products" 
    ON products FOR SELECT 
    USING (auth.uid() = vendor_id);

CREATE POLICY "Vendors can insert own products" 
    ON products FOR INSERT 
    WITH CHECK (auth.uid() = vendor_id);

CREATE POLICY "Vendors can update own products" 
    ON products FOR UPDATE 
    USING (auth.uid() = vendor_id);

CREATE POLICY "Vendors can delete own products" 
    ON products FOR DELETE 
    USING (auth.uid() = vendor_id);

-- Transactions: Vendors can view their transactions
-- Buyers can view via access token (handled by backend)
CREATE POLICY "Vendors can view own transactions" 
    ON transactions FOR SELECT 
    USING (auth.uid() = vendor_id);

-- Payouts: Vendors can view their payouts
CREATE POLICY "Vendors can view own payouts" 
    ON payouts FOR SELECT 
    USING (auth.uid() = vendor_id);

-- Disputes: Vendors can view their disputes
CREATE POLICY "Vendors can view own disputes" 
    ON disputes FOR SELECT 
    USING (
        EXISTS (
            SELECT 1 FROM transactions t 
            WHERE t.id = disputes.transaction_id 
            AND t.vendor_id = auth.uid()
        )
    );

-- Events: Vendors can view events for their transactions
CREATE POLICY "Vendors can view own events" 
    ON transaction_events FOR SELECT 
    USING (
        EXISTS (
            SELECT 1 FROM transactions t 
            WHERE t.id = transaction_events.transaction_id 
            AND t.vendor_id = auth.uid()
        )
    );

-- Notifications: Users can view their notifications
CREATE POLICY "Users can view own notifications" 
    ON notification_logs FOR SELECT 
    USING (
        recipient_type = 'vendor' 
        AND EXISTS (
            SELECT 1 FROM transactions t 
            WHERE t.id = notification_logs.transaction_id 
            AND t.vendor_id = auth.uid()
        )
    );

-- Public Metrics: Anyone can view (for trust badges)
CREATE POLICY "Public metrics are viewable by all" 
    ON vendor_public_metrics FOR SELECT 
    USING (true);

-- ============================================
-- FUNCTIONS & TRIGGERS
-- ============================================

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at trigger to all tables
CREATE TRIGGER update_vendors_updated_at BEFORE UPDATE ON vendors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_transactions_updated_at BEFORE UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_payouts_updated_at BEFORE UPDATE ON payouts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_disputes_updated_at BEFORE UPDATE ON disputes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_vendor_metrics_updated_at BEFORE UPDATE ON vendor_public_metrics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Auto-create vendor profile on auth user creation
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.vendors (id, email, username, display_name)
    VALUES (
        NEW.id, 
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'username', SPLIT_PART(NEW.email, '@', 1)),
        COALESCE(NEW.raw_user_meta_data->>'full_name', SPLIT_PART(NEW.email, '@', 1))
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger for new user signup
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Transaction event logging trigger
CREATE OR REPLACE FUNCTION log_transaction_event()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO transaction_events (
        transaction_id,
        actor_type,
        actor_id,
        event_type,
        payload
    ) VALUES (
        NEW.id,
        'system',
        NULL,
        'transaction_' || LOWER(REPLACE(NEW.status::text, ' ', '_')),
        jsonb_build_object(
            'old_status', OLD.status,
            'new_status', NEW.status,
            'amount_ngn', NEW.amount_ngn,
            'vendor_id', NEW.vendor_id
        )
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER on_transaction_status_change
    AFTER UPDATE OF status ON transactions
    FOR EACH ROW
    WHEN (OLD.status IS DISTINCT FROM NEW.status)
    EXECUTE FUNCTION log_transaction_event();

-- ============================================
-- VIEWS FOR CONVENIENCE
-- ============================================

-- Vendor dashboard view
CREATE VIEW vendor_dashboard AS
SELECT 
    v.id as vendor_id,
    v.username,
    v.display_name,
    v.status,
    v.payout_ready,
    COALESCE(vm.protected_sales_count, 0) as total_sales,
    COALESCE(vm.released_volume_ngn, 0) as total_volume,
    COALESCE(vm.successful_payouts_count, 0) as successful_payouts,
    (SELECT COUNT(*) FROM transactions t WHERE t.vendor_id = v.id AND t.status = 'FUNDS_LOCKED') as funds_locked_count,
    (SELECT COALESCE(SUM(t.vendor_net_ngn), 0) FROM transactions t WHERE t.vendor_id = v.id AND t.status = 'FUNDS_LOCKED') as funds_locked_amount,
    (SELECT COUNT(*) FROM transactions t WHERE t.vendor_id = v.id AND t.status = 'DISPUTED') as disputed_count
FROM vendors v
LEFT JOIN vendor_public_metrics vm ON v.id = vm.vendor_id;

-- Transactions with full details
CREATE VIEW transaction_details AS
SELECT 
    t.*,
    v.username as vendor_username,
    v.display_name as vendor_display_name,
    p.name as product_name_current,
    d.status as dispute_status,
    d.reason_code as dispute_reason,
    ps.status as payout_status
FROM transactions t
JOIN vendors v ON t.vendor_id = v.id
LEFT JOIN products p ON t.product_id = p.id
LEFT JOIN disputes d ON t.id = d.transaction_id
LEFT JOIN payouts ps ON t.id = ps.transaction_id;

-- ============================================
-- INITIAL DATA (Optional)
-- ============================================

-- Insert initial enum values or reference data if needed
-- (Leave empty for production, populate via seeds)

-- ============================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================

COMMENT ON TABLE vendors IS 'Vendor profiles extending Supabase Auth users';
COMMENT ON TABLE transactions IS 'Payment transactions with state machine per BRD Section 9';
COMMENT ON TABLE payouts IS 'Vendor payout records via Paystack Transfer API';
COMMENT ON TABLE disputes IS 'Buyer-vendor dispute cases with evidence';
COMMENT ON TABLE transaction_events IS 'Immutable audit log for all transaction state changes';
COMMENT ON TABLE vendor_public_metrics IS 'Denormalized trust metrics for public badges';

COMMENT ON COLUMN transactions.status IS 'State machine: PENDING_PAYMENT -> FUNDS_LOCKED -> AWAITING_BUYER_CONFIRMATION -> RELEASED/REFUNDED';
COMMENT ON COLUMN transactions.auto_release_at IS '24-hour countdown starts after vendor marks delivered (BRD Section 11)';
COMMENT ON COLUMN transactions.paystack_reference IS 'Paystack transaction reference for idempotency';
COMMENT ON COLUMN payouts.transfer_reference IS 'Paystack transfer reference for idempotency (Architecture & Regulation Section 2)';
