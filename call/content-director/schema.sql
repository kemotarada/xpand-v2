ALTER TABLE xpand_content_campaigns ADD COLUMN IF NOT EXISTS kind TEXT NOT NULL DEFAULT 'campaign';
ALTER TABLE xpand_content_campaigns ADD COLUMN IF NOT EXISTS checkpoint JSONB NOT NULL DEFAULT '{}';
ALTER TABLE xpand_content_campaigns ADD COLUMN IF NOT EXISTS idempotency_key TEXT;
ALTER TABLE xpand_content_campaigns ADD COLUMN IF NOT EXISTS worker_id UUID;
ALTER TABLE xpand_content_campaigns ADD COLUMN IF NOT EXISTS lease_until TIMESTAMPTZ;
ALTER TABLE xpand_content_campaigns ADD COLUMN IF NOT EXISTS attempts INTEGER NOT NULL DEFAULT 0;
ALTER TABLE xpand_content_campaigns ADD COLUMN IF NOT EXISTS revision INTEGER NOT NULL DEFAULT 1;
ALTER TABLE xpand_content_campaigns ADD COLUMN IF NOT EXISTS deadline_at TIMESTAMPTZ;
-- Allow an old deployment's non-leased jobs to drain during the first upgrade.
UPDATE xpand_content_campaigns SET lease_until=NOW()+INTERVAL '90 seconds'
WHERE status='running' AND worker_id IS NULL AND lease_until IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS xpand_content_request_key ON xpand_content_campaigns(user_id,idempotency_key);
CREATE INDEX IF NOT EXISTS xpand_content_queue ON xpand_content_campaigns(status,lease_until);
ALTER TABLE xpand_content_tasks ADD COLUMN IF NOT EXISTS production_at TIMESTAMPTZ;
ALTER TABLE xpand_content_tasks ADD COLUMN IF NOT EXISTS review_at TIMESTAMPTZ;
ALTER TABLE xpand_content_tasks ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1;
ALTER TABLE xpand_content_tasks ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}';
CREATE TABLE IF NOT EXISTS xpand_director_records (
 id UUID PRIMARY KEY, user_id BIGINT NOT NULL, kind TEXT NOT NULL, record_key TEXT NOT NULL,
 data JSONB NOT NULL, version INTEGER NOT NULL DEFAULT 1,
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 UNIQUE(user_id,kind,record_key)
);
CREATE TABLE IF NOT EXISTS xpand_director_calls (
 id UUID PRIMARY KEY,user_id BIGINT NOT NULL,campaign_id UUID REFERENCES xpand_content_campaigns(id),
 provider TEXT NOT NULL,stage TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'reserved',
 reserved_usd NUMERIC NOT NULL DEFAULT 0,usage JSONB,result JSONB,error TEXT,
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),completed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS xpand_director_budget ON xpand_director_calls(user_id,created_at);
CREATE TABLE IF NOT EXISTS xpand_director_versions (
 id UUID PRIMARY KEY,user_id BIGINT NOT NULL,entity_id UUID NOT NULL,kind TEXT NOT NULL,
 snapshot JSONB NOT NULL,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
