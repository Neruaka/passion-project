-- ============================================================================
-- PASSION — Personal AI Operating System
-- Complete database schema (reference)
-- PostgreSQL 16+ with pgvector extension
-- ============================================================================
-- This file is the human-readable reference. The source of truth for actual
-- schema changes is the Alembic migrations in backend/migrations/versions/.
-- ============================================================================

-- Required extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "vector";     -- pgvector for RAG embeddings


-- ============================================================================
-- GROUP 1 — AUTH & SYSTEM
-- ============================================================================

CREATE TABLE llm_config (
    id                      SMALLINT PRIMARY KEY DEFAULT 1,
    navichat_model          VARCHAR(50)  NOT NULL DEFAULT 'claude-sonnet-4-5',
    daily_call_budget       INT          NOT NULL DEFAULT 50,
    daily_cost_budget_eur   NUMERIC(6,2) NOT NULL DEFAULT 1.50,
    routing_enabled         BOOLEAN      NOT NULL DEFAULT TRUE,
    updated_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT singleton_llm_config CHECK (id = 1)
);

CREATE TABLE notification_config (
    id              SMALLINT     PRIMARY KEY DEFAULT 1,
    email_enabled   BOOLEAN      NOT NULL DEFAULT TRUE,
    push_enabled    BOOLEAN      NOT NULL DEFAULT TRUE,
    briefing_hour   TIME         NOT NULL DEFAULT '07:00',
    ntfy_topic      VARCHAR(200),
    recipient_email VARCHAR(255),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT singleton_notif_config CHECK (id = 1)
);

CREATE TABLE auth_attempts (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    ip_address      INET,
    attempt_type    VARCHAR(20)  NOT NULL,  -- 'login' | 'system_access'
    success         BOOLEAN      NOT NULL,
    attempted_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_auth_attempts_ip_time ON auth_attempts(ip_address, attempted_at DESC);

-- Partitioned by quarter on created_at
CREATE TABLE agent_actions (
    id               UUID         DEFAULT gen_random_uuid(),
    agent_name       VARCHAR(50)  NOT NULL,
    action_type      VARCHAR(50)  NOT NULL,
    input            JSONB,
    output           JSONB,
    prompt_sent      TEXT,
    llm_response_raw TEXT,
    tokens_used      INT,
    cost_eur         NUMERIC(8,5),
    duration_ms      INT,
    status           VARCHAR(20)  NOT NULL,  -- 'success' | 'error' | 'partial'
    error_message    TEXT,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

CREATE TABLE agent_actions_2026q2 PARTITION OF agent_actions
    FOR VALUES FROM ('2026-04-01') TO ('2026-07-01');
CREATE TABLE agent_actions_2026q3 PARTITION OF agent_actions
    FOR VALUES FROM ('2026-07-01') TO ('2026-10-01');

CREATE INDEX idx_agent_actions_created_name ON agent_actions(created_at DESC, agent_name);


-- ============================================================================
-- GROUP 2 — WORKOUTS & EXERCISES
-- ============================================================================

CREATE TABLE exercise_templates (
    hevy_id                 VARCHAR(50)  PRIMARY KEY,
    title                   VARCHAR(200) NOT NULL,
    primary_muscle_group    VARCHAR(50),
    secondary_muscle_groups VARCHAR(50)[],
    equipment               VARCHAR(50),
    exercise_type           VARCHAR(50),
    created_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE workouts (
    id              UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    hevy_id         VARCHAR(50)   UNIQUE NOT NULL,
    title           VARCHAR(200),
    description     TEXT,
    start_time      TIMESTAMPTZ   NOT NULL,
    end_time        TIMESTAMPTZ,
    hevy_created_at TIMESTAMPTZ,
    hevy_updated_at TIMESTAMPTZ,
    total_volume_kg NUMERIC(10,2),
    synced_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    raw_data        JSONB
);
CREATE INDEX idx_workouts_start_time ON workouts(start_time DESC);
CREATE INDEX idx_workouts_raw_data ON workouts USING GIN (raw_data);

CREATE TABLE workout_exercises (
    id                   UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    workout_id           UUID         NOT NULL REFERENCES workouts(id) ON DELETE CASCADE,
    exercise_template_id VARCHAR(50)  REFERENCES exercise_templates(hevy_id),
    title                VARCHAR(200),
    order_index          INT          NOT NULL,
    notes                TEXT,
    superset_id          VARCHAR(50)
);
CREATE INDEX idx_workout_exercises_workout ON workout_exercises(workout_id, order_index);

CREATE TABLE workout_sets (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    workout_exercise_id UUID         NOT NULL REFERENCES workout_exercises(id) ON DELETE CASCADE,
    order_index         INT          NOT NULL,
    set_type            VARCHAR(20)  NOT NULL DEFAULT 'normal',  -- warmup|normal|failure|dropset
    weight_kg           NUMERIC(6,2),
    reps                INT,
    rpe                 NUMERIC(3,1),
    distance_meters     NUMERIC(8,2),
    duration_seconds    INT
);
CREATE INDEX idx_workout_sets_exercise ON workout_sets(workout_exercise_id, order_index);

CREATE TABLE sync_state (
    id                   SMALLINT     GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    service              VARCHAR(50)  UNIQUE NOT NULL,  -- 'hevy' | 'cronometer' | 'health'
    last_successful_sync TIMESTAMPTZ,
    bootstrap_completed  BOOLEAN      NOT NULL DEFAULT FALSE,
    last_error           TEXT,
    last_error_at        TIMESTAMPTZ,
    updated_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);


-- ============================================================================
-- GROUP 3 — TARGETS & CONTEXT
-- ============================================================================

CREATE TABLE training_context (
    id                          SMALLINT     PRIMARY KEY DEFAULT 1,
    phase                       VARCHAR(20),  -- cutting|bulking|maintenance|recomp
    phase_started_at            DATE,
    phase_target_end_date       DATE,
    current_weight_kg           NUMERIC(5,2),
    current_body_fat_pct        NUMERIC(4,1),
    target_weight_kg            NUMERIC(5,2),
    target_body_fat_pct         NUMERIC(4,1),
    daily_kcal_target           INT,
    daily_protein_g_target_min  INT,
    daily_protein_g_target_max  INT,
    daily_hydration_l_target    NUMERIC(3,1),
    sleep_target_hours_min      NUMERIC(3,1),
    sleep_target_hours_max      NUMERIC(3,1),
    bedtime_target              TIME,
    wakeup_target               TIME,
    daily_steps_target          INT,
    weekly_long_walks_target    INT,
    weekly_session_target       INT,
    active_split                VARCHAR(50),
    supplements                 JSONB,
    notes                       TEXT,
    updated_at                  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT singleton_training_context CHECK (id = 1)
);

CREATE TABLE exercise_targets (
    id                       UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    exercise_template_id     VARCHAR(50)  REFERENCES exercise_templates(hevy_id),
    exercise_title           VARCHAR(200),
    baseline_weight_kg       NUMERIC(6,2),
    baseline_reps            INT,
    baseline_1rm_estimate    NUMERIC(6,2),
    baseline_recorded_at     TIMESTAMPTZ,
    target_weight_kg_min     NUMERIC(6,2),
    target_weight_kg_max     NUMERIC(6,2),
    target_reps_min          INT,
    target_reps_max          INT,
    target_1rm_estimate      NUMERIC(6,2),
    estimated_weeks_min      INT,
    estimated_weeks_max      INT,
    set_at                   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    expected_completion_date DATE,
    exercise_type            VARCHAR(30),
    track_1rm                BOOLEAN      NOT NULL DEFAULT TRUE,
    track_volume             BOOLEAN      NOT NULL DEFAULT TRUE,
    track_reps               BOOLEAN      NOT NULL DEFAULT TRUE,
    workout_day              VARCHAR(20),
    progression_chain        JSONB,
    bodyweight_dependent     BOOLEAN      NOT NULL DEFAULT FALSE,
    bw_threshold_kg          NUMERIC(5,2),
    context_phase            VARCHAR(20),
    notes                    TEXT,
    status                   VARCHAR(20)  NOT NULL DEFAULT 'active',
    achieved_at              TIMESTAMPTZ,
    created_at               TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at               TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_exercise_targets_status ON exercise_targets(status) WHERE status = 'active';

CREATE TABLE program_split (
    id               SMALLINT     PRIMARY KEY DEFAULT 1,
    split_name       VARCHAR(50),
    monday           VARCHAR(20),
    tuesday          VARCHAR(20),
    wednesday        VARCHAR(20),
    thursday         VARCHAR(20),
    friday           VARCHAR(20),
    saturday         VARCHAR(20),
    sunday           VARCHAR(20),
    day_compositions JSONB,
    active_since     DATE,
    active_until     DATE,
    notes            TEXT,
    CONSTRAINT singleton_program_split CHECK (id = 1)
);


-- ============================================================================
-- GROUP 4 — ANALYSIS
-- ============================================================================

CREATE TABLE personal_records (
    id                   UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    exercise_template_id VARCHAR(50)   REFERENCES exercise_templates(hevy_id),
    exercise_title       VARCHAR(200),
    pr_type              VARCHAR(30)   NOT NULL,  -- one_rep_max|reps_at_load|session_volume|muscle_group_volume
    new_value            NUMERIC(10,2) NOT NULL,
    old_value            NUMERIC(10,2),
    gain                 NUMERIC(10,2),
    bucket               VARCHAR(20),
    workout_id           UUID          REFERENCES workouts(id) ON DELETE SET NULL,
    workout_set_id       UUID          REFERENCES workout_sets(id) ON DELETE SET NULL,
    achieved_at          TIMESTAMPTZ   NOT NULL,
    created_at           TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_prs_exercise_time ON personal_records(exercise_template_id, achieved_at DESC);
CREATE INDEX idx_prs_type ON personal_records(pr_type, achieved_at DESC);

CREATE TABLE exercise_analysis (
    id                   UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    exercise_template_id VARCHAR(50)  REFERENCES exercise_templates(hevy_id),
    exercise_title       VARCHAR(200),
    analysis_type        VARCHAR(30)  NOT NULL,  -- plateau_official|plateau_stalled|regression|behind_schedule
    severity             VARCHAR(20),  -- minor|moderate|major
    details              JSONB,
    status               VARCHAR(20)  NOT NULL DEFAULT 'active',
    resolved_at          TIMESTAMPTZ,
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_analysis_active ON exercise_analysis(status, analysis_type) WHERE status = 'active';

CREATE TABLE weekly_stats (
    id                      UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    week_start              DATE          UNIQUE NOT NULL,
    total_sessions          INT           NOT NULL DEFAULT 0,
    total_duration_minutes  INT           NOT NULL DEFAULT 0,
    total_volume_kg         NUMERIC(12,2) NOT NULL DEFAULT 0,
    volume_per_muscle_group JSONB,
    pr_count                INT           NOT NULL DEFAULT 0,
    created_at              TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE TABLE monthly_stats (
    id                      UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    month_start             DATE          UNIQUE NOT NULL,
    total_sessions          INT           NOT NULL DEFAULT 0,
    total_duration_minutes  INT           NOT NULL DEFAULT 0,
    total_volume_kg         NUMERIC(12,2) NOT NULL DEFAULT 0,
    volume_per_muscle_group JSONB,
    pr_count                INT           NOT NULL DEFAULT 0,
    created_at              TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);


-- ============================================================================
-- GROUP 5 — HEALTH
-- ============================================================================

-- Partitioned by quarter on recorded_at
CREATE TABLE health_metrics (
    id               UUID          DEFAULT gen_random_uuid(),
    recorded_at      TIMESTAMPTZ   NOT NULL,
    duration_seconds INT,
    metric_type      VARCHAR(50)   NOT NULL,
    numeric_value    NUMERIC(12,4),
    unit             VARCHAR(20),
    source           VARCHAR(30)   NOT NULL,  -- health_connect|manual|lab|dexcom
    source_device    VARCHAR(50),
    source_app       VARCHAR(50),
    metadata         JSONB,
    source_record_id VARCHAR(200),
    ingested_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, recorded_at),
    CONSTRAINT uq_health_source_record UNIQUE (source, source_record_id, recorded_at)
) PARTITION BY RANGE (recorded_at);

CREATE TABLE health_metrics_2026q2 PARTITION OF health_metrics
    FOR VALUES FROM ('2026-04-01') TO ('2026-07-01');
CREATE TABLE health_metrics_2026q3 PARTITION OF health_metrics
    FOR VALUES FROM ('2026-07-01') TO ('2026-10-01');

CREATE INDEX idx_health_metrics_type_time ON health_metrics(metric_type, recorded_at DESC);
CREATE INDEX idx_health_metrics_recorded_brin ON health_metrics USING BRIN (recorded_at);
CREATE INDEX idx_health_metrics_metadata ON health_metrics USING GIN (metadata);

CREATE MATERIALIZED VIEW daily_health_summary AS
SELECT
    date_trunc('day', recorded_at)::date AS day,
    COALESCE(SUM(CASE WHEN metric_type='sleep_session' THEN duration_seconds END) / 3600.0, 0) AS sleep_hours,
    COALESCE(SUM(CASE WHEN metric_type='steps' THEN numeric_value END), 0) AS total_steps,
    AVG(CASE WHEN metric_type='heart_rate' THEN numeric_value END) AS hr_avg,
    MIN(CASE WHEN metric_type='heart_rate' THEN numeric_value END) AS hr_min,
    AVG(CASE WHEN metric_type='resting_hr' THEN numeric_value END) AS resting_hr,
    AVG(CASE WHEN metric_type='hrv_rmssd' THEN numeric_value END) AS hrv_rmssd_avg
FROM health_metrics
GROUP BY date_trunc('day', recorded_at);
CREATE UNIQUE INDEX idx_daily_health_summary_day ON daily_health_summary(day);

CREATE TABLE health_markers (
    id                 UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    measurement_date   DATE         NOT NULL,
    measurement_type   VARCHAR(30)  NOT NULL,  -- blood_panel|body_composition|cgm_summary|other
    source             VARCHAR(100),
    values             JSONB        NOT NULL,
    normalized_metrics JSONB,
    fasting_state      BOOLEAN,
    notes              TEXT,
    attachment_path    VARCHAR(500),
    created_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_health_markers_date ON health_markers(measurement_date DESC);


-- ============================================================================
-- GROUP 6 — COACHING
-- ============================================================================

CREATE TABLE workout_suggestions (
    id                    UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    generated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    for_date              DATE         NOT NULL,
    prompt_used           TEXT,
    llm_response_raw      JSONB,
    recommendation        TEXT,
    reasoning             TEXT,
    workout_type          VARCHAR(20),
    exercises             JSONB,
    expected_duration_min INT,
    warnings              JSONB,
    alternative_if_tired  TEXT,
    status                VARCHAR(20)  NOT NULL DEFAULT 'pending',  -- pending|accepted|modified|rejected
    user_feedback         TEXT,
    user_modifications    JSONB,
    tokens_used           INT,
    cost_eur              NUMERIC(8,5)
);
CREATE INDEX idx_workout_suggestions_date ON workout_suggestions(for_date DESC);

CREATE TABLE nutrition_plans (
    id                     UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    for_date               DATE         NOT NULL,
    generated_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    daily_kcal_target      INT,
    daily_protein_target_g INT,
    daily_carbs_target_g   INT,
    daily_fats_target_g    INT,
    hydration_target_l     NUMERIC(3,1),
    timing_strategy        VARCHAR(50),
    meal_distribution      JSONB,
    supplements_today      JSONB,
    is_training_day        BOOLEAN      NOT NULL,
    notes                  TEXT
);
CREATE INDEX idx_nutrition_plans_date ON nutrition_plans(for_date DESC);

CREATE TABLE challenges (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    week_start      DATE         NOT NULL,
    title           VARCHAR(200) NOT NULL,
    description     TEXT,
    challenge_type  VARCHAR(50),
    measurable_goal JSONB,
    tracking_method VARCHAR(20),  -- auto|manual
    xp_reward       INT          NOT NULL DEFAULT 0,
    deadline        TIMESTAMPTZ,
    status          VARCHAR(20)  NOT NULL DEFAULT 'active',
    completed_at    TIMESTAMPTZ,
    progress        JSONB,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_challenges_week ON challenges(week_start DESC, status);


-- ============================================================================
-- GROUP 7 — GAMIFICATION
-- ============================================================================

CREATE TABLE missions (
    id           UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    for_date     DATE         NOT NULL,
    title        VARCHAR(200) NOT NULL,
    description  TEXT,
    mission_type VARCHAR(50),
    xp_reward    INT          NOT NULL DEFAULT 0,
    status       VARCHAR(20)  NOT NULL DEFAULT 'pending',
    completed_at TIMESTAMPTZ,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_missions_date ON missions(for_date DESC, status);

CREATE TABLE xp_log (
    id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type VARCHAR(30)  NOT NULL,  -- mission|challenge|pr|...
    source_id   UUID,
    xp_earned   INT          NOT NULL,
    notes       TEXT,
    earned_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_xp_log_earned ON xp_log(earned_at DESC);

CREATE TABLE user_level (
    id              SMALLINT    PRIMARY KEY DEFAULT 1,
    current_xp      INT         NOT NULL DEFAULT 0,
    current_level   VARCHAR(20) NOT NULL DEFAULT 'Recruit',
    total_xp_earned INT         NOT NULL DEFAULT 0,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT singleton_user_level CHECK (id = 1)
);

CREATE TABLE streaks (
    id                      UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    streak_type             VARCHAR(20)  UNIQUE NOT NULL,  -- workout|nutrition|sleep
    current_value           INT          NOT NULL DEFAULT 0,
    best_value              INT          NOT NULL DEFAULT 0,
    frozen_until            DATE,
    freezes_used_this_month INT          NOT NULL DEFAULT 0,
    last_calculated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);


-- ============================================================================
-- GROUP 8 — MEMORY & CHAT
-- ============================================================================

CREATE TABLE agent_memory (
    id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    content     TEXT         NOT NULL,
    embedding   VECTOR(1536),
    tags        VARCHAR(50)[],
    source      VARCHAR(20)  NOT NULL DEFAULT 'implicit',  -- explicit|implicit|manual
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    expires_at  TIMESTAMPTZ,
    is_obsolete BOOLEAN      NOT NULL DEFAULT FALSE
);
CREATE INDEX idx_agent_memory_embedding ON agent_memory USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_agent_memory_tags ON agent_memory USING GIN (tags);
CREATE INDEX idx_agent_memory_active ON agent_memory(created_at DESC) WHERE is_obsolete = FALSE;

CREATE TABLE conversations (
    id                UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_type VARCHAR(20)  NOT NULL,  -- direct_line|coach_fitness
    started_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    last_message_at   TIMESTAMPTZ
);
CREATE INDEX idx_conversations_last_msg ON conversations(last_message_at DESC);

CREATE TABLE messages (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID         NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            VARCHAR(20)  NOT NULL,  -- user|assistant|system
    content         TEXT         NOT NULL,
    tokens_used     INT,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at);

-- ============================================================================
-- SEED singletons (insert default rows)
-- ============================================================================
INSERT INTO llm_config (id) VALUES (1) ON CONFLICT DO NOTHING;
INSERT INTO notification_config (id) VALUES (1) ON CONFLICT DO NOTHING;
INSERT INTO training_context (id) VALUES (1) ON CONFLICT DO NOTHING;
INSERT INTO program_split (id) VALUES (1) ON CONFLICT DO NOTHING;
INSERT INTO user_level (id) VALUES (1) ON CONFLICT DO NOTHING;
INSERT INTO sync_state (service) VALUES ('hevy'), ('cronometer'), ('health') ON CONFLICT DO NOTHING;
INSERT INTO streaks (streak_type) VALUES ('workout'), ('nutrition'), ('sleep') ON CONFLICT DO NOTHING;

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
