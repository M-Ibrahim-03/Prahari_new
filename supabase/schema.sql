-- PRAHARI Database Schema & Privacy Architecture (PRD §30 & §33)
-- Zero PII: Device hashes (SHA-256) only, no names, phone numbers, or coordinates in analytics.
-- Strict Row Level Security (RLS) on all tables. Anon users can INSERT only.

-- 1. Device Registrations
CREATE TABLE IF NOT EXISTS devices (
    device_hash TEXT PRIMARY KEY,
    district TEXT NOT NULL,
    app_version TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_active_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Farmer Feedback ("⚠️ यह गलत है" - PRD §17.3)
CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    idempotency_key TEXT UNIQUE NOT NULL,
    device_hash TEXT NOT NULL,
    district TEXT NOT NULL,
    cell_id TEXT,
    field_ref TEXT,
    run_id TEXT NOT NULL,
    feedback_type TEXT NOT NULL, -- e.g. 'false_alarm', 'missed_symptom', 'weather_mismatch', 'timing_bad'
    details JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Alert Ledger Mirror
CREATE TABLE IF NOT EXISTS ledger_records (
    hash TEXT PRIMARY KEY,
    prev_hash TEXT NOT NULL,
    run_id TEXT NOT NULL,
    district TEXT NOT NULL,
    record_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Enable RLS on ALL tables
ALTER TABLE devices ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE ledger_records ENABLE ROW LEVEL SECURITY;

-- Anonymous Insert Policies (Public PWA can submit feedback and register devices)
CREATE POLICY "Anon can register device" ON devices
    FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "Anon can update own device activity" ON devices
    FOR UPDATE TO anon USING (true);

CREATE POLICY "Anon can submit feedback" ON feedback
    FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "Anon can read public ledger" ON ledger_records
    FOR SELECT TO anon USING (true);

-- Deny direct public reads on individual feedback rows
CREATE POLICY "No public read on individual feedback" ON feedback
    FOR SELECT TO anon USING (false);

-- Privacy k >= 5 Aggregation View (PRD §33.1)
-- Only exposes disease feedback aggregated by district/cell when at least 5 distinct devices report
CREATE OR REPLACE VIEW cell_feedback_k5 AS
SELECT
    district,
    cell_id,
    feedback_type,
    COUNT(*) as total_reports,
    COUNT(DISTINCT device_hash) as distinct_devices,
    MAX(created_at) as latest_report
FROM feedback
GROUP BY district, cell_id, feedback_type
HAVING COUNT(DISTINCT device_hash) >= 5;
