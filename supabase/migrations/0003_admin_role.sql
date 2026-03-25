-- SurePay Admin Role and Security Features
-- Version: 1.0.0
-- Date: March 25, 2026

-- ============================================
-- ADMIN ROLE EXTENSIONS
-- ============================================

-- Add role column to vendors table
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'vendor' 
CHECK (role IN ('vendor', 'admin', 'super_admin'));

-- Create admin_sessions for 2FA tracking
CREATE TABLE IF NOT EXISTS admin_sessions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  otp_code TEXT NOT NULL,
  otp_verified BOOLEAN DEFAULT false,
  expires_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create admin_action_log for audit trail
CREATE TABLE IF NOT EXISTS admin_action_log (
  id BIGSERIAL PRIMARY KEY,
  admin_id UUID REFERENCES auth.users(id),
  action_type TEXT NOT NULL,
  target_type TEXT,
  target_id UUID,
  details JSONB DEFAULT '{}',
  ip_address TEXT,
  user_agent TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE admin_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_action_log ENABLE ROW LEVEL SECURITY;

-- Admin-only RLS policies (service role bypass)
CREATE POLICY "Admins can view all vendors"
  ON vendors FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM vendors v2 
      WHERE v2.id = auth.uid() 
      AND v2.role IN ('admin', 'super_admin')
    )
  );

CREATE POLICY "Admins can update vendor status"
  ON vendors FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM vendors v2 
      WHERE v2.id = auth.uid() 
      AND v2.role IN ('admin', 'super_admin')
    )
  );

-- Function to check admin status
CREATE OR REPLACE FUNCTION is_admin()
RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM vendors 
    WHERE id = auth.uid() 
    AND role IN ('admin', 'super_admin')
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE;

-- Function to log admin actions
CREATE OR REPLACE FUNCTION log_admin_action(
  p_admin_id UUID,
  p_action_type TEXT,
  p_target_type TEXT,
  p_target_id UUID,
  p_details JSONB DEFAULT '{}'
)
RETURNS void AS $$
BEGIN
  INSERT INTO admin_action_log (
    admin_id,
    action_type,
    target_type,
    target_id,
    details,
    ip_address,
    user_agent
  ) VALUES (
    p_admin_id,
    p_action_type,
    p_target_type,
    p_target_id,
    p_details,
    current_setting('request.header.x-forwarded-for', true),
    current_setting('request.header.user-agent', true)
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

-- Indexes for admin tables
CREATE INDEX IF NOT EXISTS idx_admin_sessions_user_id ON admin_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_admin_sessions_expires ON admin_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_admin_action_log_admin_id ON admin_action_log(admin_id);
CREATE INDEX IF NOT EXISTS idx_admin_action_log_action_type ON admin_action_log(action_type);
CREATE INDEX IF NOT EXISTS idx_admin_action_log_created_at ON admin_action_log(created_at);
CREATE INDEX IF NOT EXISTS idx_vendors_role ON vendors(role);

-- ============================================
-- INITIAL DATA
-- ============================================

-- Insert default admin user (will be updated with actual user ID during seeding)
-- This is a placeholder - actual admin user will be created via backend or manually

-- ============================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================

COMMENT ON TABLE admin_sessions IS 'Admin 2FA session tracking for sensitive operations';
COMMENT ON TABLE admin_action_log IS 'Immutable audit log of all admin actions';
COMMENT ON COLUMN vendors.role IS 'User role: vendor, admin, or super_admin';