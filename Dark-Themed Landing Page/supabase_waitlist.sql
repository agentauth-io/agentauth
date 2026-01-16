-- Waitlist table for beta access control
-- Run this in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS waitlist (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  status TEXT DEFAULT 'approved' CHECK (status IN ('pending', 'approved', 'rejected')),
  beta_access BOOLEAN DEFAULT TRUE,  -- Auto-approve for now
  invite_code TEXT UNIQUE DEFAULT CONCAT('AA-', UPPER(SUBSTRING(MD5(RANDOM()::TEXT) FROM 1 FOR 8))),
  source TEXT DEFAULT 'website',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  approved_at TIMESTAMPTZ DEFAULT NOW(),
  last_email_sent_at TIMESTAMPTZ
);

-- Create indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_waitlist_email ON waitlist(email);
CREATE INDEX IF NOT EXISTS idx_waitlist_status ON waitlist(status);
CREATE INDEX IF NOT EXISTS idx_waitlist_beta_access ON waitlist(beta_access);

-- Row Level Security (RLS)
ALTER TABLE waitlist ENABLE ROW LEVEL SECURITY;

-- Allow anyone to insert (for waitlist signups)
CREATE POLICY "Allow public insert" ON waitlist
  FOR INSERT WITH CHECK (true);

-- Allow authenticated users to read their own entry
CREATE POLICY "Users can read own waitlist" ON waitlist
  FOR SELECT USING (auth.jwt() ->> 'email' = email);

-- Allow service role full access (for admin operations)
CREATE POLICY "Service role full access" ON waitlist
  FOR ALL USING (auth.role() = 'service_role');

-- Grant public access for signup
GRANT INSERT ON waitlist TO anon;
GRANT SELECT ON waitlist TO authenticated;

-- Function to check beta access
CREATE OR REPLACE FUNCTION check_beta_access(user_email TEXT)
RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM waitlist 
    WHERE email = user_email 
    AND beta_access = TRUE
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
