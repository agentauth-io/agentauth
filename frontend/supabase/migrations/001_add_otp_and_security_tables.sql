-- OTP verification codes table
-- Run this in your Supabase SQL editor

CREATE TABLE IF NOT EXISTS otp_codes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  code VARCHAR(6) NOT NULL,
  type VARCHAR(10) NOT NULL CHECK (type IN ('email', 'sms')),
  destination VARCHAR(255) NOT NULL,
  expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
  used_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for quick lookups
CREATE INDEX IF NOT EXISTS idx_otp_codes_destination ON otp_codes(destination);
CREATE INDEX IF NOT EXISTS idx_otp_codes_code ON otp_codes(code);
CREATE INDEX IF NOT EXISTS idx_otp_codes_expires_at ON otp_codes(expires_at);

-- User security preferences table
CREATE TABLE IF NOT EXISTS user_security_settings (
  user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  two_factor_enabled BOOLEAN DEFAULT FALSE,
  two_factor_method VARCHAR(10) CHECK (two_factor_method IN ('email', 'sms', 'totp')),
  phone_number VARCHAR(20),
  phone_verified BOOLEAN DEFAULT FALSE,
  backup_codes TEXT[],
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE otp_codes ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_security_settings ENABLE ROW LEVEL SECURITY;

-- RLS Policies for otp_codes
-- Users can only see their own OTP codes
CREATE POLICY "Users can view own OTP codes" ON otp_codes
  FOR SELECT USING (auth.uid() = user_id);

-- Service role can insert OTP codes (via Netlify functions)
CREATE POLICY "Service role can insert OTP codes" ON otp_codes
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Service role can update OTP codes" ON otp_codes
  FOR UPDATE USING (true);

CREATE POLICY "Service role can delete OTP codes" ON otp_codes
  FOR DELETE USING (true);

-- RLS Policies for user_security_settings
CREATE POLICY "Users can view own security settings" ON user_security_settings
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update own security settings" ON user_security_settings
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Service role can upsert security settings" ON user_security_settings
  FOR ALL USING (true);

-- Grant access to authenticated users
GRANT SELECT ON otp_codes TO authenticated;
GRANT SELECT, UPDATE ON user_security_settings TO authenticated;

-- Grant full access to service role
GRANT ALL ON otp_codes TO service_role;
GRANT ALL ON user_security_settings TO service_role;
