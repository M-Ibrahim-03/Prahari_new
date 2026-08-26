-- PRAHARI Database Schema & Privacy Architecture (PRD §30 & §33)
-- Zero PII: device hashes only. No names, phone numbers, or field coordinates leave the phone.
--
-- 🔴 Re-runnable. Every statement is idempotent so this file can be pasted into the Supabase SQL
-- editor repeatedly during a build. Bare CREATE POLICY is NOT idempotent — it raises
-- "policy already exists" and aborts the rest of the script, which previously left the GRANTs at
-- the bottom unapplied and the k>=5 view silently unreadable.

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
    feedback_type TEXT NOT NULL, -- 'false_alarm' | 'missed_symptom' | 'weather_mismatch' | 'timing_bad'
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

-- Enable RLS on ALL tables. Without this, the anon key is a full read/write key on every row.
ALTER TABLE devices       ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback      ENABLE ROW LEVEL SECURITY;
ALTER TABLE ledger_records ENABLE ROW LEVEL SECURITY;

-- ── Policies ────────────────────────────────────────────────────────────────────────────────────
DROP POLICY IF EXISTS "Anon can register device" ON devices;
CREATE POLICY "Anon can register device" ON devices
    FOR INSERT TO anon WITH CHECK (true);

-- 🔴 Scoped only by row existence, because there is no authenticated identity to scope it to:
-- device_hash is generated client-side in localStorage, so any anon caller could present any hash.
-- The blast radius is deliberately capped by what the row holds — district, app version, and a
-- last-seen timestamp, all non-PII (§33). Anything that could identify or locate a farmer must
-- never be added to this table, because this policy cannot protect it.
DROP POLICY IF EXISTS "Anon can update own device activity" ON devices;
CREATE POLICY "Anon can update own device activity" ON devices
    FOR UPDATE TO anon USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Anon can submit feedback" ON feedback;
CREATE POLICY "Anon can submit feedback" ON feedback
    FOR INSERT TO anon WITH CHECK (true);

-- 🔴 Write-only for anon. A farmer's individual correction is never readable back through the
-- public key, only through the k>=5 aggregate view below.
DROP POLICY IF EXISTS "No public read on individual feedback" ON feedback;
CREATE POLICY "No public read on individual feedback" ON feedback
    FOR SELECT TO anon USING (false);

-- The alert ledger is public on purpose: it is the accountability record the Trust screen verifies.
DROP POLICY IF EXISTS "Anon can read public ledger" ON ledger_records;
CREATE POLICY "Anon can read public ledger" ON ledger_records
    FOR SELECT TO anon USING (true);

-- ── Privacy k >= 5 Aggregation View (PRD §33.1) ─────────────────────────────────────────────────
-- Exposes feedback counts only where at least 5 distinct devices reported the same cell, so no
-- single farmer's report can be isolated.
--
-- 🔴 Left as a NON-security_invoker view deliberately. It runs with the owner's rights and so
-- bypasses the "No public read" policy on feedback — that bypass IS the mechanism, and the HAVING
-- clause is what makes it safe. Adding `WITH (security_invoker = true)` would make the view obey
-- the caller's policy, return zero rows for anon, and break the aggregate.
CREATE OR REPLACE VIEW cell_feedback_k5 AS
SELECT
    district,
    cell_id,
    feedback_type,
    COUNT(*)                       AS total_reports,
    COUNT(DISTINCT device_hash)    AS distinct_devices,
    MAX(created_at)                AS latest_report
FROM feedback
GROUP BY district, cell_id, feedback_type
HAVING COUNT(DISTINCT device_hash) >= 5;

-- 🔴 RLS governs tables; GRANTs govern reachability. The view had neither a policy nor a grant, so
-- anon got "permission denied for view cell_feedback_k5" — the k>=5 aggregate was unreadable by the
-- only role that ever queries it.
GRANT SELECT ON cell_feedback_k5 TO anon;

-- Table-level grants. RLS still filters every row; these only make the tables addressable.
GRANT INSERT         ON devices       TO anon;
GRANT UPDATE         ON devices       TO anon;
GRANT INSERT, SELECT ON feedback      TO anon;  -- SELECT is gated to false by policy above
GRANT SELECT         ON ledger_records TO anon;
