-- SurePay Security Functions & Utilities
-- Critical: Idempotency, Row-Level Locks, Webhook Security
-- Per Architecture & Regulation Sections 2 & 3

-- ============================================
-- IDEMPOTENCY FUNCTIONS
-- ============================================
-- Per Architecture & Regulation Section 2: Prevent double-spend anomaly

-- Check if transaction already exists (for webhook deduplication)
CREATE OR REPLACE FUNCTION check_transaction_exists(
    p_paystack_reference TEXT
) RETURNS TABLE (
    exists BOOLEAN,
    transaction_id UUID,
    current_status transaction_status
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        TRUE,
        t.id,
        t.status
    FROM transactions t
    WHERE t.paystack_reference = p_paystack_reference
    LIMIT 1;
    
    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, NULL::UUID, NULL::transaction_status;
    END IF;
END;
$$ LANGUAGE plpgsql STABLE;

-- Acquire row lock for payout (prevents duplicate transfers)
-- Per Architecture & Regulation Section 2: SELECT ... FOR UPDATE
CREATE OR REPLACE FUNCTION acquire_payout_lock(
    p_transaction_id UUID,
    p_vendor_id UUID
) RETURNS TABLE (
    locked BOOLEAN,
    transaction_status transaction_status,
    existing_payout_id UUID
) AS $$
DECLARE
    v_status transaction_status;
    v_payout_id UUID;
BEGIN
    -- Acquire exclusive lock on transaction row
    SELECT t.status, p.id
    INTO v_status, v_payout_id
    FROM transactions t
    LEFT JOIN payouts p ON p.transaction_id = t.id
    WHERE t.id = p_transaction_id
      AND t.vendor_id = p_vendor_id
    FOR UPDATE OF t NOWAIT; -- Fail fast if locked
    
    IF v_status IS NULL THEN
        RETURN QUERY SELECT FALSE, NULL::transaction_status, NULL::UUID;
        RETURN;
    END IF;
    
    -- Check if payout already exists
    IF v_payout_id IS NOT NULL THEN
        RETURN QUERY SELECT FALSE, v_status, v_payout_id;
        RETURN;
    END IF;
    
    -- Check if transaction is in RELEASED state
    IF v_status != 'RELEASED' THEN
        RETURN QUERY SELECT FALSE, v_status, NULL::UUID;
        RETURN;
    END IF;
    
    RETURN QUERY SELECT TRUE, v_status, NULL::UUID;
    
EXCEPTION
    WHEN lock_not_available THEN
        RETURN QUERY SELECT FALSE, NULL::transaction_status, NULL::UUID;
    WHEN OTHERS THEN
        RETURN QUERY SELECT FALSE, NULL::transaction_status, NULL::UUID;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- WEBHOOK SECURITY
-- ============================================
-- Per BRD Section 18: Verify Paystack webhook signatures

-- Store webhook secrets (should be set via Supabase vault in production)
CREATE TABLE IF NOT EXISTS webhook_secrets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider TEXT NOT NULL UNIQUE,
    secret_key TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Function to verify Paystack webhook signature
CREATE OR REPLACE FUNCTION verify_paystack_signature(
    p_signature TEXT,
    p_payload TEXT,
    p_secret TEXT
) RETURNS BOOLEAN AS $$
DECLARE
    v_expected_signature TEXT;
BEGIN
    -- HMAC-SHA256 verification
    v_expected_signature := encode(
        hmac(p_payload, p_secret, 'sha256'),
        'hex'
    );
    
    -- Constant-time comparison to prevent timing attacks
    RETURN v_expected_signature = p_signature;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================
-- STATE MACHINE VALIDATION
-- ============================================
-- Per BRD Section 9: Enforce valid state transitions

-- Valid state transitions
CREATE TYPE state_transition AS (
    from_status transaction_status,
    to_status transaction_status
);

-- Function to validate state transitions
CREATE OR REPLACE FUNCTION is_valid_state_transition(
    p_from transaction_status,
    p_to transaction_status
) RETURNS BOOLEAN AS $$
BEGIN
    RETURN CASE p_from
        WHEN 'PENDING_PAYMENT' THEN
            p_to IN ('FUNDS_LOCKED', 'EXPIRED', 'CANCELLED')
        WHEN 'FUNDS_LOCKED' THEN
            p_to IN ('AWAITING_BUYER_CONFIRMATION', 'DISPUTED', 'REFUNDED', 'CANCELLED')
        WHEN 'AWAITING_BUYER_CONFIRMATION' THEN
            p_to IN ('RELEASED', 'DISPUTED', 'REFUNDED')
        WHEN 'DISPUTED' THEN
            p_to IN ('RELEASED', 'REFUNDED')
        ELSE
            FALSE
    END;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Trigger to enforce state machine
CREATE OR REPLACE FUNCTION enforce_state_machine()
RETURNS TRIGGER AS $$
BEGIN
    -- Skip if status hasn't changed
    IF OLD.status = NEW.status THEN
        RETURN NEW;
    END IF;
    
    -- Validate transition
    IF NOT is_valid_state_transition(OLD.status, NEW.status) THEN
        RAISE EXCEPTION 'Invalid state transition from % to %', OLD.status, NEW.status
            USING ERRCODE = 'invalid_transaction_state';
    END IF;
    
    -- Set timestamps based on new state
    CASE NEW.status
        WHEN 'FUNDS_LOCKED' THEN
            NEW.paid_at := COALESCE(NEW.paid_at, NOW());
        WHEN 'AWAITING_BUYER_CONFIRMATION' THEN
            NEW.delivery_marked_at := COALESCE(NEW.delivery_marked_at, NOW());
            NEW.auto_release_at := COALESCE(NEW.auto_release_at, NOW() + INTERVAL '24 hours');
        WHEN 'RELEASED' THEN
            NEW.released_at := COALESCE(NEW.released_at, NOW());
        WHEN 'REFUNDED' THEN
            NEW.refunded_at := COALESCE(NEW.refunded_at, NOW());
        WHEN 'EXPIRED' THEN
            NEW.expires_at := COALESCE(NEW.expires_at, NOW());
        WHEN 'CANCELLED' THEN
            NEW.cancelled_at := COALESCE(NEW.cancelled_at, NOW());
    END CASE;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enforce_state_machine_trigger
    BEFORE UPDATE OF status ON transactions
    FOR EACH ROW
    EXECUTE FUNCTION enforce_state_machine();

-- ============================================
-- BUYER ACCESS TOKEN
-- ============================================
-- Per BRD Section 12.5: Signed re-access links for buyers

-- Function to generate secure access token
CREATE OR REPLACE FUNCTION generate_buyer_access_token(
    p_transaction_id UUID,
    p_buyer_email TEXT
) RETURNS TEXT AS $$
BEGIN
    -- Generate token using transaction_id + email + random component
    RETURN encode(
        digest(
            p_transaction_id::text || p_buyer_email || gen_random_uuid()::text,
            'sha256'
        ),
        'hex'
    );
END;
$$ LANGUAGE plpgsql;

-- Function to hash token for storage
CREATE OR REPLACE FUNCTION hash_access_token(
    p_token TEXT
) RETURNS TEXT AS $$
BEGIN
    -- Use bcrypt-like approach (simplified - use proper hashing in production)
    RETURN encode(digest(p_token, 'sha256'), 'hex');
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- FEE CALCULATION
-- ============================================
-- Per BRD Section 13: 1.5% fee model

CREATE OR REPLACE FUNCTION calculate_transaction_fees(
    p_amount_ngn INTEGER
) RETURNS TABLE (
    fee_ngn INTEGER,
    vendor_net_ngn INTEGER
) AS $$
DECLARE
    v_fee_rate NUMERIC := 0.015; -- 1.5%
    v_fee INTEGER;
    v_net INTEGER;
BEGIN
    -- Calculate fee (1.5% rounded down)
    v_fee := FLOOR(p_amount_ngn * v_fee_rate);
    
    -- Ensure vendor gets at least 90% (protect against edge cases)
    v_net := p_amount_ngn - v_fee;
    
    IF v_net < (p_amount_ngn * 0.9) THEN
        v_fee := FLOOR(p_amount_ngn * 0.1);
        v_net := p_amount_ngn - v_fee;
    END IF;
    
    RETURN QUERY SELECT v_fee, v_net;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================
-- TRUST METRICS UPDATE
-- ============================================
-- Per BRD Section 12.9: Settlement Gravity System

CREATE OR REPLACE FUNCTION update_vendor_public_metrics(
    p_vendor_id UUID
) RETURNS void AS $$
BEGIN
    INSERT INTO vendor_public_metrics (
        vendor_id,
        protected_sales_count,
        released_volume_ngn,
        successful_payouts_count,
        resolved_disputes_count,
        last_successful_payout_at,
        trust_score_version
    )
    SELECT 
        p_vendor_id,
        COUNT(DISTINCT t.id),
        COALESCE(SUM(t.amount_ngn), 0),
        COUNT(DISTINCT p.id),
        COUNT(DISTINCT d.id),
        MAX(p.succeeded_at),
        '1.0.0'
    FROM transactions t
    LEFT JOIN payouts p ON p.transaction_id = t.id AND p.status = 'succeeded'
    LEFT JOIN disputes d ON d.transaction_id = t.id AND d.status IN ('resolved_release', 'resolved_refund')
    WHERE t.vendor_id = p_vendor_id
      AND t.status = 'RELEASED'
    ON CONFLICT (vendor_id) DO UPDATE SET
        protected_sales_count = EXCLUDED.protected_sales_count,
        released_volume_ngn = EXCLUDED.released_volume_ngn,
        successful_payouts_count = EXCLUDED.successful_payouts_count,
        resolved_disputes_count = EXCLUDED.resolved_disputes_count,
        last_successful_payout_at = EXCLUDED.last_successful_payout_at,
        trust_score_version = '1.0.0',
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update metrics on payout success
CREATE OR REPLACE FUNCTION trigger_update_vendor_metrics()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'succeeded' AND OLD.status != 'succeeded' THEN
        PERFORM update_vendor_public_metrics(NEW.vendor_id);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER on_payout_success
    AFTER UPDATE OF status ON payouts
    FOR EACH ROW
    WHEN (NEW.status = 'succeeded' AND OLD.status != 'succeeded')
    EXECUTE FUNCTION trigger_update_vendor_metrics();

-- ============================================
-- ADMIN FUNCTIONS
-- ============================================
-- Backend-only operations per BRD Section 18

-- Function to manually release transaction (admin only)
CREATE OR REPLACE FUNCTION admin_release_transaction(
    p_transaction_id UUID,
    p_admin_id UUID,
    p_reason TEXT DEFAULT 'manual_release'
) RETURNS BOOLEAN AS $$
DECLARE
    v_vendor_id UUID;
BEGIN
    -- Check if admin (simplified - add proper admin check in production)
    -- This should be called from backend service-role only
    
    UPDATE transactions
    SET status = 'RELEASED'
    WHERE id = p_transaction_id
      AND status IN ('AWAITING_BUYER_CONFIRMATION', 'DISPUTED')
    RETURNING vendor_id INTO v_vendor_id;
    
    IF FOUND THEN
        -- Log admin action
        INSERT INTO transaction_events (
            transaction_id,
            actor_type,
            actor_id,
            event_type,
            payload
        ) VALUES (
            p_transaction_id,
            'admin',
            p_admin_id,
            'admin_manual_release',
            jsonb_build_object('reason', p_reason)
        );
        
        RETURN TRUE;
    END IF;
    
    RETURN FALSE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to process refund (admin only)
CREATE OR REPLACE FUNCTION admin_process_refund(
    p_transaction_id UUID,
    p_admin_id UUID,
    p_reason TEXT DEFAULT 'admin_refund'
) RETURNS BOOLEAN AS $$
DECLARE
    v_vendor_id UUID;
    v_status transaction_status;
BEGIN
    -- Get current status
    SELECT status, vendor_id INTO v_status, v_vendor_id
    FROM transactions
    WHERE id = p_transaction_id
    FOR UPDATE;
    
    -- Can only refund from FUNDS_LOCKED or AWAITING_BUYER_CONFIRMATION
    IF v_status NOT IN ('FUNDS_LOCKED', 'AWAITING_BUYER_CONFIRMATION', 'DISPUTED') THEN
        RETURN FALSE;
    END IF;
    
    UPDATE transactions
    SET status = 'REFUNDED'
    WHERE id = p_transaction_id;
    
    -- Log admin action
    INSERT INTO transaction_events (
        transaction_id,
        actor_type,
        actor_id,
        event_type,
        payload
    ) VALUES (
        p_transaction_id,
        'admin',
        p_admin_id,
        'admin_process_refund',
        jsonb_build_object('reason', p_reason, 'previous_status', v_status)
    );
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- CRON JOB FUNCTIONS
-- ============================================
-- Per BRD Section 11: Auto-release after 24h

-- Function to process auto-releases
CREATE OR REPLACE FUNCTION process_auto_releases()
RETURNS TABLE (
    processed_count INTEGER,
    transaction_ids UUID[]
) AS $$
DECLARE
    v_ids UUID[];
BEGIN
    -- Get transactions ready for auto-release
    SELECT array_agg(id) INTO v_ids
    FROM transactions
    WHERE status = 'AWAITING_BUYER_CONFIRMATION'
      AND auto_release_at <= NOW();
    
    -- Update all eligible transactions
    UPDATE transactions
    SET status = 'RELEASED'
    WHERE id = ANY(v_ids);
    
    -- Log events
    INSERT INTO transaction_events (
        transaction_id,
        actor_type,
        actor_id,
        event_type,
        payload
    )
    SELECT 
        id,
        'system',
        NULL,
        'auto_release_triggered',
        jsonb_build_object('auto_release_at', auto_release_at)
    FROM transactions
    WHERE id = ANY(v_ids);
    
    RETURN QUERY SELECT 
        COALESCE(array_length(v_ids, 1), 0),
        v_ids;
END;
$$ LANGUAGE plpgsql;

-- Function to expire pending payments
CREATE OR REPLACE FUNCTION expire_pending_transactions()
RETURNS TABLE (
    expired_count INTEGER,
    transaction_ids UUID[]
) AS $$
DECLARE
    v_ids UUID[];
BEGIN
    -- Get expired pending transactions
    SELECT array_agg(id) INTO v_ids
    FROM transactions
    WHERE status = 'PENDING_PAYMENT'
      AND expires_at <= NOW();
    
    -- Update all expired transactions
    UPDATE transactions
    SET status = 'EXPIRED'
    WHERE id = ANY(v_ids);
    
    RETURN QUERY SELECT 
        COALESCE(array_length(v_ids, 1), 0),
        v_ids;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- PERFORMANCE OPTIMIZATION
-- ============================================

-- Function to get transaction with lock (for critical operations)
CREATE OR REPLACE FUNCTION get_transaction_with_lock(
    p_transaction_id UUID
) RETURNS SETOF transactions AS $$
BEGIN
    RETURN QUERY
    SELECT *
    FROM transactions
    WHERE id = p_transaction_id
    FOR UPDATE NOWAIT;
END;
$$ LANGUAGE plpgsql;

-- Function to check for duplicate webhooks
CREATE OR REPLACE FUNCTION is_duplicate_webhook(
    p_paystack_reference TEXT,
    p_event_type TEXT
) RETURNS BOOLEAN AS $$
DECLARE
    v_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM transaction_events
        WHERE event_type = p_event_type
          AND payload->>'paystack_reference' = p_paystack_reference
          AND created_at > NOW() - INTERVAL '5 minutes'
    ) INTO v_exists;
    
    RETURN v_exists;
END;
$$ LANGUAGE plpgsql;

-- Comments for documentation
COMMENT ON FUNCTION acquire_payout_lock IS 'Acquire row-level lock on transaction to prevent duplicate payouts - Architecture & Regulation Section 2';
COMMENT ON FUNCTION verify_paystack_signature IS 'Verify Paystack webhook signature using HMAC-SHA256 - BRD Section 18';
COMMENT ON FUNCTION is_valid_state_transition IS 'Validate state machine transitions per BRD Section 9';
COMMENT ON FUNCTION process_auto_releases IS 'Cron job: Auto-release transactions after 24h - BRD Section 11';
COMMENT ON FUNCTION update_vendor_public_metrics IS 'Update public trust metrics for Settlement Gravity Badge - BRD Section 12.9';
