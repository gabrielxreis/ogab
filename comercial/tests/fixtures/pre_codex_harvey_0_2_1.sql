-- Database written by Mariana 0.2.1 (commit 7940da4, before the Codex provider):
-- one contacted prospect, one Claude call and its usage event, one setting.
PRAGMA user_version = 10;
BEGIN TRANSACTION;
CREATE TABLE actions (
        id TEXT PRIMARY KEY,
        action_type TEXT,
        agent TEXT,
        details_json TEXT DEFAULT '{}',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
CREATE TABLE campaigns (
        id TEXT PRIMARY KEY,
        name TEXT DEFAULT '',
        channel TEXT DEFAULT 'email',
        instantly_campaign_id TEXT DEFAULT '',
        sequence_json TEXT DEFAULT '[]',
        prospect_ids_json TEXT DEFAULT '[]',
        status TEXT DEFAULT 'draft',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
CREATE TABLE companies (
        id TEXT PRIMARY KEY,
        name TEXT DEFAULT '',
        domain TEXT DEFAULT '',
        website TEXT DEFAULT '',
        description TEXT DEFAULT '',
        industry TEXT DEFAULT '',
        company_size TEXT DEFAULT '',
        location TEXT DEFAULT '',
        source TEXT DEFAULT '',
        source_url TEXT DEFAULT '',
        notes TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    , tech_stack_json TEXT DEFAULT '[]', signals_json TEXT DEFAULT '[]', external_id TEXT DEFAULT '', phone TEXT DEFAULT '', prospects_checked_at TIMESTAMP DEFAULT NULL, profile_checked_at TIMESTAMP DEFAULT NULL);
CREATE TABLE conversations (
        id TEXT PRIMARY KEY,
        prospect_id TEXT REFERENCES prospects(id),
        campaign_id TEXT DEFAULT '',
        channel TEXT DEFAULT 'email',
        thread_json TEXT DEFAULT '[]',
        intent TEXT DEFAULT '',
        stage TEXT DEFAULT 'initial_outreach',
        status TEXT DEFAULT 'open',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
CREATE TABLE email_patterns (
        domain TEXT PRIMARY KEY,
        pattern TEXT DEFAULT '',
        source TEXT DEFAULT '',
        confidence REAL DEFAULT 0.0,
        mx_type TEXT DEFAULT '',
        is_catch_all INTEGER DEFAULT -1,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
CREATE TABLE feedback (
        id TEXT PRIMARY KEY,
        entity_type TEXT DEFAULT '',
        entity_id TEXT DEFAULT '',
        comment TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
CREATE TABLE observations (
        id TEXT PRIMARY KEY,
        company_id TEXT DEFAULT '',
        prospect_id TEXT DEFAULT '',
        signal_code TEXT NOT NULL,
        collector TEXT DEFAULT '',
        value_num REAL,
        value_text TEXT DEFAULT '',
        confidence REAL DEFAULT 1.0,
        evidence_url TEXT DEFAULT '',
        observed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        run_id TEXT DEFAULT ''
    );
CREATE TABLE outbox (
        id TEXT PRIMARY KEY,
        campaign_id TEXT DEFAULT '',
        prospect_id TEXT DEFAULT '',
        conversation_id TEXT DEFAULT '',
        step INTEGER DEFAULT 1,
        kind TEXT DEFAULT 'sequence',
        to_email TEXT DEFAULT '',
        subject TEXT DEFAULT '',
        body TEXT DEFAULT '',
        status TEXT DEFAULT 'pending_review',
        send_at TIMESTAMP,
        sent_at TIMESTAMP,
        provider TEXT DEFAULT '',
        message_id TEXT DEFAULT '',
        thread_ref TEXT DEFAULT '',
        in_reply_to TEXT DEFAULT '',
        error TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
CREATE TABLE processed_replies (
        reply_id TEXT PRIMARY KEY,
        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
CREATE TABLE prospects (
        id TEXT PRIMARY KEY,
        company_id TEXT DEFAULT '' REFERENCES companies(id),
        first_name TEXT DEFAULT '',
        last_name TEXT DEFAULT '',
        email TEXT DEFAULT '',
        email_verified INTEGER DEFAULT 0,
        phone TEXT DEFAULT '',
        phone_verified INTEGER DEFAULT 0,
        linkedin_url TEXT DEFAULT '',
        title TEXT DEFAULT '',
        seniority TEXT DEFAULT '',
        department TEXT DEFAULT '',
        source TEXT DEFAULT '',
        source_url TEXT DEFAULT '',
        status TEXT DEFAULT 'new',
        score INTEGER DEFAULT 0,
        personalization_notes TEXT DEFAULT '',
        company TEXT DEFAULT '',
        industry TEXT DEFAULT '',
        company_size TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    , email_status TEXT DEFAULT '');
INSERT INTO "prospects" VALUES('5a3c0bac997f','','Old','Lead','old@legacy.com',1,'',0,'','CTO','','','','','contacted',0,'','Legacy','','','2026-10-13T17:12:16.602805','2026-10-13T17:12:16.603130','verified');
CREATE TABLE runs (
        id TEXT PRIMARY KEY,
        stage TEXT DEFAULT '',
        status TEXT DEFAULT 'running',
        provider TEXT DEFAULT '',
        records INTEGER DEFAULT 0,
        cost_usd REAL DEFAULT 0.0,
        params_json TEXT DEFAULT '{}',
        error TEXT DEFAULT '',
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ended_at TIMESTAMP
    );
CREATE TABLE settings (
        key TEXT PRIMARY KEY,
        value TEXT DEFAULT '',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
INSERT INTO "settings" VALUES('some_flag','1','2026-10-13 17:12:16');
CREATE TABLE signal_codes (
        code TEXT PRIMARY KEY,
        label TEXT DEFAULT '',
        description TEXT DEFAULT '',
        category TEXT DEFAULT '',
        value_type TEXT DEFAULT 'text',
        collector TEXT DEFAULT '',
        cost_note TEXT DEFAULT '',
        status TEXT DEFAULT 'proposed',
        confidence_floor REAL DEFAULT 0.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
CREATE TABLE usage_events (
        id TEXT PRIMARY KEY,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        agent TEXT DEFAULT '',
        task TEXT DEFAULT '',
        session_id TEXT DEFAULT '',
        request_key TEXT DEFAULT '',
        model TEXT DEFAULT '',
        input_tokens INTEGER DEFAULT 0,
        output_tokens INTEGER DEFAULT 0,
        cache_read_tokens INTEGER DEFAULT 0,
        cache_creation_tokens INTEGER DEFAULT 0,
        cost_usd REAL DEFAULT 0.0,
        duration_ms INTEGER DEFAULT 0,
        num_turns INTEGER DEFAULT 0,
        is_error INTEGER DEFAULT 0,
        source TEXT DEFAULT 'result_json'
    );
INSERT INTO "usage_events" VALUES('04e31ac435e4','2026-10-13 17:12:16','writer','write_sequence','s-old','','claude-sonnet',10,5,0,0,0.01,0,0,0,'result_json');
CREATE TABLE usage_log (
        id TEXT PRIMARY KEY,
        date TEXT UNIQUE,
        claude_calls INTEGER DEFAULT 0,
        usage_percent REAL DEFAULT 0.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
INSERT INTO "usage_log" VALUES('4596fa453fa2','2026-10-13',1,0.0,'2026-10-13 17:12:16');
CREATE INDEX idx_companies_domain ON companies(domain);
CREATE INDEX idx_prospects_company_id ON prospects(company_id);
CREATE INDEX idx_prospects_status ON prospects(status);
CREATE INDEX idx_prospects_email ON prospects(email);
CREATE INDEX idx_campaigns_status ON campaigns(status);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_feedback_entity ON feedback(entity_type, entity_id);
CREATE INDEX idx_usage_date ON usage_log(date);
CREATE UNIQUE INDEX uq_prospects_email
        ON prospects(email) WHERE email != '';
CREATE UNIQUE INDEX uq_prospects_linkedin
        ON prospects(linkedin_url) WHERE linkedin_url != '';
CREATE UNIQUE INDEX uq_companies_domain
        ON companies(domain) WHERE domain != '';
CREATE INDEX idx_conversations_campaign_id ON conversations(campaign_id);
CREATE INDEX idx_conversations_prospect_id ON conversations(prospect_id);
CREATE INDEX idx_conversations_intent ON conversations(intent);
CREATE INDEX idx_prospects_name_company
        ON prospects(LOWER(first_name), LOWER(last_name), LOWER(company));
CREATE INDEX idx_prospects_status_updated ON prospects(status, updated_at);
CREATE INDEX idx_actions_created_at ON actions(created_at);
CREATE INDEX idx_usage_events_created ON usage_events(created_at);
CREATE INDEX idx_usage_events_agent ON usage_events(agent);
CREATE INDEX idx_usage_events_session ON usage_events(session_id);
CREATE UNIQUE INDEX uq_usage_events_request
        ON usage_events(request_key) WHERE request_key != '';
CREATE UNIQUE INDEX uq_outbox_campaign_step
        ON outbox(campaign_id, prospect_id, step)
        WHERE campaign_id != '' AND kind = 'sequence';
CREATE INDEX idx_outbox_status_send_at ON outbox(status, send_at);
CREATE INDEX idx_outbox_prospect ON outbox(prospect_id);
CREATE INDEX idx_obs_company ON observations(company_id);
CREATE INDEX idx_obs_signal ON observations(signal_code);
CREATE INDEX idx_obs_company_signal
        ON observations(company_id, signal_code, observed_at);
CREATE INDEX idx_obs_run ON observations(run_id);
CREATE TRIGGER trg_observations_signal_known
    BEFORE INSERT ON observations
    FOR EACH ROW
    WHEN NEW.signal_code NOT IN (SELECT code FROM signal_codes)
    BEGIN
        SELECT RAISE(ABORT, 'unknown signal_code: not in signal_codes vocabulary');
    END;
CREATE INDEX idx_runs_stage_started ON runs(stage, started_at);
CREATE UNIQUE INDEX uq_companies_external
        ON companies(external_id) WHERE external_id != '';
COMMIT;
