-- Nexus One — Enterprise Autonomous Execution OS extension schema
-- Apply after database/schema.sql

-- ---------------------------------------------------------------------------
-- Subscription plans
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS subscription_plans (
    id                  SERIAL PRIMARY KEY,
    name                VARCHAR(100) NOT NULL UNIQUE,
    slug                VARCHAR(50) NOT NULL UNIQUE,
    price_monthly_cents INTEGER NOT NULL DEFAULT 0,
    runtime_minutes_day INTEGER NOT NULL DEFAULT 5,
    max_agents          INTEGER NOT NULL DEFAULT 2,
    features            JSONB NOT NULL DEFAULT '[]',
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO subscription_plans (name, slug, price_monthly_cents, runtime_minutes_day, max_agents, features) VALUES
    ('Free', 'free', 0, 5, 2, '["basic_objectives"]'),
    ('Standard', 'standard', 2900, 60, 5, '["basic_objectives","workforce_board"]'),
    ('Professional', 'professional', 9900, 480, 99, '["mission_control","executive_reports","evidence_engine","all_agents"]'),
    ('Business', 'business', 29900, 1440, 99, '["teams","approvals","audit_logs","mission_control","executive_reports"]'),
    ('Enterprise', 'enterprise', 0, 99999, 99, '["custom_pricing","sso","dedicated_support","unlimited_runtime"]')
ON CONFLICT (slug) DO NOTHING;

CREATE TABLE IF NOT EXISTS tenant_subscriptions (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id               UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    plan_id                 INTEGER NOT NULL REFERENCES subscription_plans(id),
    status                  VARCHAR(50) NOT NULL DEFAULT 'active',
    coupon_code             VARCHAR(50),
    current_period_start    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    current_period_end      TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_tenant_subscription UNIQUE (tenant_id)
);

CREATE INDEX IF NOT EXISTS idx_tenant_subscriptions_tenant ON tenant_subscriptions (tenant_id);

-- ---------------------------------------------------------------------------
-- Coupons
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS coupons (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code                VARCHAR(50) NOT NULL UNIQUE,
    description         TEXT,
    discount_type       VARCHAR(20) NOT NULL CHECK (discount_type IN ('percentage', 'fixed', 'trial_extension')),
    discount_value      NUMERIC(10,2) NOT NULL DEFAULT 0,
    trial_extension_days INTEGER DEFAULT 0,
    max_uses            INTEGER,
    used_count          INTEGER NOT NULL DEFAULT 0,
    expires_at          TIMESTAMPTZ,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO coupons (code, description, discount_type, discount_value, max_uses, expires_at) VALUES
    ('WELCOME50', '50% off first month', 'percentage', 50, 1000, NOW() + INTERVAL '1 year'),
    ('STARTUP25', '25% off Standard plan', 'percentage', 25, 500, NOW() + INTERVAL '6 months'),
    ('EARLYACCESS', '30-day trial extension', 'trial_extension', 0, 200, NOW() + INTERVAL '1 year'),
    ('INVESTORDEMO', 'Investor demo — Professional trial', 'trial_extension', 0, 50, NOW() + INTERVAL '2 years')
ON CONFLICT (code) DO NOTHING;

UPDATE coupons SET trial_extension_days = 30 WHERE code IN ('EARLYACCESS', 'INVESTORDEMO');

CREATE TABLE IF NOT EXISTS coupon_redemptions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    coupon_id   UUID NOT NULL REFERENCES coupons(id),
    tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id     UUID NOT NULL REFERENCES users(id),
    redeemed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_coupon_tenant UNIQUE (coupon_id, tenant_id)
);

-- ---------------------------------------------------------------------------
-- Business objectives (replaces task-centric model)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS business_objectives (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id               UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    created_by              UUID NOT NULL REFERENCES users(id),
    title                   VARCHAR(255) NOT NULL,
    description             TEXT NOT NULL,
    category                VARCHAR(100),
    complexity              VARCHAR(20) CHECK (complexity IN ('low', 'medium', 'high', 'critical')),
    status                  VARCHAR(50) NOT NULL DEFAULT 'draft',
    success_probability     NUMERIC(5,2),
    estimated_duration_hours NUMERIC(8,2),
    predicted_risk_level    VARCHAR(20),
    execution_plan          JSONB,
    selected_agents         JSONB,
    dependencies            JSONB,
    risks_detected          JSONB,
    predicted_outputs       JSONB,
    business_impact         JSONB,
    executive_summary       TEXT,
    quality_score           NUMERIC(5,2),
    current_phase           VARCHAR(50) DEFAULT 'planning',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_objectives_tenant ON business_objectives (tenant_id);
CREATE INDEX IF NOT EXISTS idx_objectives_status ON business_objectives (tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_objectives_category ON business_objectives (category);

-- ---------------------------------------------------------------------------
-- Projects (execution containers linked to objectives)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS projects (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    objective_id    UUID NOT NULL REFERENCES business_objectives(id) ON DELETE CASCADE,
    name            VARCHAR(255) NOT NULL,
    status          VARCHAR(50) NOT NULL DEFAULT 'planning',
    quality_score   NUMERIC(5,2),
    hours_saved     NUMERIC(10,2) DEFAULT 0,
    cost_savings    NUMERIC(12,2) DEFAULT 0,
    revenue_impact  NUMERIC(12,2) DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_projects_tenant ON projects (tenant_id);
CREATE INDEX IF NOT EXISTS idx_projects_objective ON projects (objective_id);

-- ---------------------------------------------------------------------------
-- Execution phases & timeline
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS execution_phases (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    objective_id    UUID NOT NULL REFERENCES business_objectives(id) ON DELETE CASCADE,
    phase_name      VARCHAR(50) NOT NULL,
    phase_order     INTEGER NOT NULL,
    status          VARCHAR(50) NOT NULL DEFAULT 'pending',
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_phases_objective ON execution_phases (objective_id);

CREATE TABLE IF NOT EXISTS timeline_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    objective_id    UUID NOT NULL REFERENCES business_objectives(id) ON DELETE CASCADE,
    phase           VARCHAR(50) NOT NULL,
    event_type      VARCHAR(100) NOT NULL,
    message         TEXT NOT NULL,
    status          VARCHAR(50) NOT NULL DEFAULT 'info',
    agent_key       VARCHAR(100),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_timeline_objective ON timeline_events (objective_id, created_at DESC);

-- ---------------------------------------------------------------------------
-- Evidence engine
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS evidence_records (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    objective_id    UUID NOT NULL REFERENCES business_objectives(id) ON DELETE CASCADE,
    project_id      UUID REFERENCES projects(id) ON DELETE SET NULL,
    agent_key       VARCHAR(100) NOT NULL,
    agent_name      VARCHAR(255) NOT NULL,
    action          VARCHAR(255) NOT NULL,
    input_summary   TEXT,
    output_summary  TEXT,
    reason          TEXT,
    impact          TEXT,
    metadata        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_evidence_objective ON evidence_records (objective_id);
CREATE INDEX IF NOT EXISTS idx_evidence_tenant ON evidence_records (tenant_id);
CREATE INDEX IF NOT EXISTS idx_evidence_agent ON evidence_records (agent_key);

-- ---------------------------------------------------------------------------
-- Enterprise memory graph
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS memory_graph_nodes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    objective_id    UUID REFERENCES business_objectives(id) ON DELETE SET NULL,
    node_type       VARCHAR(50) NOT NULL,
    title           VARCHAR(255) NOT NULL,
    content         JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_memory_nodes_tenant ON memory_graph_nodes (tenant_id);
CREATE INDEX IF NOT EXISTS idx_memory_nodes_type ON memory_graph_nodes (node_type);
CREATE INDEX IF NOT EXISTS idx_memory_nodes_objective ON memory_graph_nodes (objective_id);

CREATE TABLE IF NOT EXISTS memory_graph_edges (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    source_id       UUID NOT NULL REFERENCES memory_graph_nodes(id) ON DELETE CASCADE,
    target_id       UUID NOT NULL REFERENCES memory_graph_nodes(id) ON DELETE CASCADE,
    relationship    VARCHAR(100) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_memory_edges_source ON memory_graph_edges (source_id);
CREATE INDEX IF NOT EXISTS idx_memory_edges_target ON memory_graph_edges (target_id);

-- ---------------------------------------------------------------------------
-- Risks & executive insights
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS objective_risks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    objective_id    UUID NOT NULL REFERENCES business_objectives(id) ON DELETE CASCADE,
    risk_type       VARCHAR(100) NOT NULL,
    severity        VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    description     TEXT NOT NULL,
    mitigation      TEXT,
    is_resolved     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_risks_objective ON objective_risks (objective_id);

CREATE TABLE IF NOT EXISTS executive_insights (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    objective_id        UUID NOT NULL REFERENCES business_objectives(id) ON DELETE CASCADE,
    summary             TEXT NOT NULL,
    strategic_insights  JSONB,
    recommendations     JSONB,
    roi_analysis        JSONB,
    impact_report       JSONB,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_insights_objective ON executive_insights (objective_id);

-- ---------------------------------------------------------------------------
-- Runtime usage tracking (subscription enforcement)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS runtime_usage (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    usage_date      DATE NOT NULL DEFAULT CURRENT_DATE,
    minutes_used    NUMERIC(10,2) NOT NULL DEFAULT 0,
    CONSTRAINT uq_runtime_tenant_date UNIQUE (tenant_id, usage_date)
);

CREATE INDEX IF NOT EXISTS idx_runtime_tenant_date ON runtime_usage (tenant_id, usage_date);
