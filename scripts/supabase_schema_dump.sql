--
-- PostgreSQL database dump
--

\restrict OBBsz3urdeIzpCT0hZ8xvVHmVG1DLkECDaHlrfqsD16vtRXKgKfDth1RMQKG5m4

-- Dumped from database version 17.6
-- Dumped by pg_dump version 17.10

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA public;


--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON SCHEMA public IS 'standard public schema';


--
-- Name: buyingintent; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.buyingintent AS ENUM (
    'low',
    'medium',
    'high'
);


--
-- Name: salesfunnelstage; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.salesfunnelstage AS ENUM (
    'new',
    'discovery',
    'qualified',
    'objection',
    'ready_to_buy',
    'converted',
    'lost'
);


--
-- Name: rls_auto_enable(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.rls_auto_enable() RETURNS event_trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog'
    AS $$
DECLARE
  cmd record;
BEGIN
  FOR cmd IN
    SELECT *
    FROM pg_event_trigger_ddl_commands()
    WHERE command_tag IN ('CREATE TABLE', 'CREATE TABLE AS', 'SELECT INTO')
      AND object_type IN ('table','partitioned table')
  LOOP
     IF cmd.schema_name IS NOT NULL AND cmd.schema_name IN ('public') AND cmd.schema_name NOT IN ('pg_catalog','information_schema') AND cmd.schema_name NOT LIKE 'pg_toast%' AND cmd.schema_name NOT LIKE 'pg_temp%' THEN
      BEGIN
        EXECUTE format('alter table if exists %s enable row level security', cmd.object_identity);
        RAISE LOG 'rls_auto_enable: enabled RLS on %', cmd.object_identity;
      EXCEPTION
        WHEN OTHERS THEN
          RAISE LOG 'rls_auto_enable: failed to enable RLS on %', cmd.object_identity;
      END;
     ELSE
        RAISE LOG 'rls_auto_enable: skip % (either system schema or not in enforced list: %.)', cmd.object_identity, cmd.schema_name;
     END IF;
  END LOOP;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: analytics_daily_rollups; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.analytics_daily_rollups (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    time_bucket timestamp with time zone NOT NULL,
    metric_name character varying(80) NOT NULL,
    dimension jsonb,
    value numeric(14,4) DEFAULT '0'::numeric NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: analytics_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.analytics_events (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    conversation_id uuid,
    customer_id uuid,
    event_type character varying(80) NOT NULL,
    source_agent character varying(50),
    target_agent character varying(50),
    event_metadata jsonb,
    idempotency_key character varying(255),
    schema_version integer DEFAULT 1 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: analytics_hourly_rollups; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.analytics_hourly_rollups (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    time_bucket timestamp with time zone NOT NULL,
    metric_name character varying(80) NOT NULL,
    dimension jsonb,
    value numeric(14,4) DEFAULT '0'::numeric NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: analytics_outbox; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.analytics_outbox (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    conversation_id uuid,
    customer_id uuid,
    event_type character varying(80) NOT NULL,
    source_agent character varying(50),
    target_agent character varying(50),
    event_metadata jsonb,
    idempotency_key character varying(255),
    schema_version integer DEFAULT 1 NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    attempts integer DEFAULT 0 NOT NULL,
    last_error text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    processed_at timestamp with time zone
);


--
-- Name: analytics_reports; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.analytics_reports (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    report_type character varying(50) NOT NULL,
    report_json jsonb NOT NULL,
    generated_at timestamp with time zone NOT NULL
);


--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audit_logs (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    user_id uuid NOT NULL,
    action character varying(255) NOT NULL,
    entity_type character varying(100),
    entity_id uuid,
    metadata jsonb,
    created_at timestamp with time zone NOT NULL
);


--
-- Name: business_insights; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.business_insights (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    title character varying NOT NULL,
    description text NOT NULL,
    category character varying NOT NULL,
    confidence numeric(5,2) NOT NULL,
    confidence_reason text,
    priority character varying NOT NULL,
    status character varying NOT NULL,
    evidence_snapshot jsonb NOT NULL,
    insight_version integer NOT NULL,
    generated_by_engine_version character varying NOT NULL,
    engine_config_version character varying NOT NULL,
    data_freshness_timestamp timestamp with time zone NOT NULL,
    snapshot_id uuid NOT NULL,
    fingerprint character varying NOT NULL,
    created_at timestamp with time zone NOT NULL
);


--
-- Name: business_question_audit; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.business_question_audit (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    question text NOT NULL,
    classification character varying NOT NULL,
    created_at timestamp with time zone NOT NULL
);


--
-- Name: business_recommendations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.business_recommendations (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    insight_id uuid NOT NULL,
    recommendation text NOT NULL,
    rationale text NOT NULL,
    confidence numeric(5,2) NOT NULL,
    priority character varying NOT NULL,
    recommendation_engine_version character varying NOT NULL,
    recommendation_rule_id character varying NOT NULL,
    effectiveness_status character varying NOT NULL,
    reviewed_at timestamp with time zone,
    review_notes text,
    created_at timestamp with time zone NOT NULL
);


--
-- Name: conversation_intelligence; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.conversation_intelligence (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    conversation_id uuid NOT NULL,
    primary_intent character varying(255),
    sentiment character varying(50),
    resolution character varying(50),
    needs_review boolean NOT NULL,
    raw_confidence numeric(5,2),
    review_reason character varying(255),
    analysis_schema_version integer NOT NULL,
    analyzer_version character varying(50) NOT NULL,
    analyzed_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


--
-- Name: conversation_intents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.conversation_intents (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    conversation_id uuid NOT NULL,
    primary_intent character varying(255) NOT NULL,
    secondary_intents jsonb NOT NULL,
    confidence numeric(5,2),
    analysis_schema_version integer NOT NULL,
    analyzer_version character varying(50) NOT NULL,
    created_at timestamp with time zone NOT NULL
);


--
-- Name: conversation_resolutions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.conversation_resolutions (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    conversation_id uuid NOT NULL,
    resolution_type character varying(50) NOT NULL,
    confidence numeric(5,2),
    needs_review boolean NOT NULL,
    analysis_schema_version integer NOT NULL,
    analyzer_version character varying(50) NOT NULL,
    analyzed_at timestamp with time zone NOT NULL
);


--
-- Name: conversation_sentiments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.conversation_sentiments (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    conversation_id uuid NOT NULL,
    sentiment character varying(50) NOT NULL,
    confidence numeric(5,2),
    needs_review boolean NOT NULL,
    analysis_schema_version integer NOT NULL,
    analyzer_version character varying(50) NOT NULL,
    analyzed_at timestamp with time zone NOT NULL
);


--
-- Name: conversation_summaries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.conversation_summaries (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    conversation_id uuid NOT NULL,
    short_summary text NOT NULL,
    long_summary text,
    summary_version integer NOT NULL,
    analysis_schema_version integer NOT NULL,
    analyzer_version character varying(50) NOT NULL,
    created_at timestamp with time zone NOT NULL
);


--
-- Name: conversation_topics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.conversation_topics (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    conversation_id uuid NOT NULL,
    topic_name character varying(255) NOT NULL,
    confidence numeric(5,2),
    needs_review boolean NOT NULL,
    analysis_schema_version integer NOT NULL,
    analyzer_version character varying(50) NOT NULL,
    created_at timestamp with time zone NOT NULL
);


--
-- Name: conversations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.conversations (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    customer_id uuid NOT NULL,
    current_agent character varying(50),
    channel character varying(50) DEFAULT 'web'::character varying NOT NULL,
    status character varying(20) DEFAULT 'active'::character varying NOT NULL,
    started_at timestamp with time zone NOT NULL,
    ended_at timestamp with time zone,
    previous_agent character varying(50),
    handoff_count integer DEFAULT 0 NOT NULL,
    last_handoff_at timestamp with time zone,
    last_handoff_reason text,
    current_state_version integer DEFAULT 1 NOT NULL,
    current_state jsonb,
    unresolved_intent character varying(50),
    loop_cooldown_until timestamp with time zone,
    external_id character varying(255)
);


--
-- Name: customer_care_cases; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.customer_care_cases (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    customer_id uuid NOT NULL,
    conversation_id uuid NOT NULL,
    complaint_type character varying(50),
    refund_requested boolean,
    refund_amount_requested numeric(12,2),
    order_id character varying(100),
    account_issue_type character varying(100),
    sentiment character varying(20),
    current_stage character varying(50) DEFAULT 'acknowledged'::character varying NOT NULL,
    escalation_reason text,
    resolution_timeline character varying(255),
    last_interaction_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    handoff_recommended boolean DEFAULT false,
    next_agent character varying(50),
    source_agent character varying(50),
    parent_case_id uuid,
    handoff_reason text,
    handoff_stage character varying(50),
    source_channel character varying(50)
);


--
-- Name: customers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.customers (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    name character varying(255) NOT NULL,
    email character varying(255),
    phone character varying(50),
    telegram_id character varying(255),
    status character varying(20) DEFAULT 'active'::character varying NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    external_id character varying(255)
);


--
-- Name: dataset_queries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dataset_queries (
    id uuid NOT NULL,
    dataset_id uuid NOT NULL,
    question text NOT NULL,
    answer text,
    chart_config jsonb,
    created_at timestamp with time zone NOT NULL
);


--
-- Name: datasets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.datasets (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    name character varying(255) NOT NULL,
    file_url text NOT NULL,
    row_count integer,
    column_count integer,
    uploaded_at timestamp with time zone NOT NULL
);


--
-- Name: document_chunks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.document_chunks (
    id uuid NOT NULL,
    document_id uuid NOT NULL,
    chunk_index integer NOT NULL,
    content text NOT NULL,
    created_at timestamp with time zone NOT NULL,
    embedding public.vector(768)
);


--
-- Name: document_chunks_backup_20_6_5; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.document_chunks_backup_20_6_5 (
    id uuid,
    document_id uuid,
    chunk_index integer,
    content text,
    created_at timestamp with time zone,
    embedding public.vector(768)
);


--
-- Name: documents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.documents (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    name character varying(255) NOT NULL,
    file_type character varying(50) NOT NULL,
    file_url text NOT NULL,
    status character varying(50) DEFAULT 'pending'::character varying NOT NULL,
    uploaded_by uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    embedding_model character varying(100),
    embedding_dim integer,
    embedded_at timestamp with time zone
);


--
-- Name: documents_backup_20_6_5; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.documents_backup_20_6_5 (
    id uuid,
    workspace_id uuid,
    name character varying(255),
    file_type character varying(50),
    file_url text,
    status character varying(50),
    uploaded_by uuid,
    created_at timestamp with time zone,
    embedding_model character varying(100),
    embedding_dim integer,
    embedded_at timestamp with time zone
);


--
-- Name: executive_reports; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.executive_reports (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    report_type character varying NOT NULL,
    report_period character varying NOT NULL,
    summary jsonb NOT NULL,
    report_version integer NOT NULL,
    generated_by_engine_version character varying NOT NULL,
    engine_config_version character varying NOT NULL,
    data_freshness_timestamp timestamp with time zone NOT NULL,
    snapshot_id uuid NOT NULL,
    fingerprint character varying NOT NULL,
    generated_at timestamp with time zone NOT NULL
);


--
-- Name: handoffs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.handoffs (
    id uuid NOT NULL,
    conversation_id uuid NOT NULL,
    from_agent character varying(50) NOT NULL,
    to_agent character varying(50) NOT NULL,
    reason text,
    created_at timestamp with time zone NOT NULL,
    workspace_id uuid,
    confidence double precision,
    trigger_intent character varying(50),
    previous_state jsonb,
    next_state jsonb,
    status character varying(20) DEFAULT 'completed'::character varying NOT NULL,
    source_message_id character varying(255),
    source_entity_type character varying(50),
    source_entity_id character varying(255),
    target_entity_type character varying(50),
    target_entity_id character varying(255)
);


--
-- Name: idempotency_keys; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.idempotency_keys (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    idempotency_key character varying NOT NULL,
    path character varying NOT NULL,
    status character varying NOT NULL,
    response_body jsonb,
    created_at timestamp with time zone NOT NULL,
    expires_at timestamp with time zone NOT NULL
);


--
-- Name: insight_lineage; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.insight_lineage (
    id uuid NOT NULL,
    insight_id uuid NOT NULL,
    source_type character varying NOT NULL,
    source_identifier character varying NOT NULL,
    source_version character varying,
    source_date_range jsonb NOT NULL,
    created_at timestamp with time zone NOT NULL
);


--
-- Name: intel_daily_intent_rollups; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.intel_daily_intent_rollups (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    time_bucket timestamp with time zone NOT NULL,
    intent_name character varying(255) NOT NULL,
    value numeric(12,2) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


--
-- Name: intel_daily_resolution_rollups; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.intel_daily_resolution_rollups (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    time_bucket timestamp with time zone NOT NULL,
    resolution_type character varying(50) NOT NULL,
    value numeric(12,2) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


--
-- Name: intel_daily_sentiment_rollups; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.intel_daily_sentiment_rollups (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    time_bucket timestamp with time zone NOT NULL,
    sentiment character varying(50) NOT NULL,
    value numeric(12,2) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


--
-- Name: intel_daily_topic_rollups; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.intel_daily_topic_rollups (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    time_bucket timestamp with time zone NOT NULL,
    topic_name character varying(255) NOT NULL,
    value numeric(12,2) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


--
-- Name: lead_profiles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lead_profiles (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    customer_id uuid NOT NULL,
    company_size character varying(100),
    budget character varying(100),
    urgency character varying(100),
    use_case character varying(500),
    buying_intent public.buyingintent,
    current_stage public.salesfunnelstage NOT NULL,
    objections jsonb,
    lead_score integer,
    last_interaction_at timestamp with time zone,
    last_stage_change_at timestamp with time zone,
    source_channel character varying(100),
    next_best_action character varying(500),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


--
-- Name: messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.messages (
    id uuid NOT NULL,
    conversation_id uuid NOT NULL,
    sender_type character varying(50) NOT NULL,
    content text NOT NULL,
    message_type character varying(50) DEFAULT 'text'::character varying NOT NULL,
    created_at timestamp with time zone NOT NULL
);


--
-- Name: notifications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.notifications (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    title character varying(255) NOT NULL,
    message text,
    type character varying(50) DEFAULT 'info'::character varying NOT NULL,
    is_read boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone NOT NULL
);


--
-- Name: public_api_key_audit; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.public_api_key_audit (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    api_key_id uuid NOT NULL,
    action character varying NOT NULL,
    old_api_key_id uuid,
    new_api_key_id uuid,
    actor_id uuid,
    reason character varying,
    "timestamp" timestamp with time zone NOT NULL
);


--
-- Name: public_api_key_rotations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.public_api_key_rotations (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    api_key_id uuid NOT NULL,
    old_key_prefix character varying(8) NOT NULL,
    new_key_prefix character varying(8) NOT NULL,
    rotated_by uuid,
    rotated_at timestamp with time zone NOT NULL
);


--
-- Name: public_api_key_scopes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.public_api_key_scopes (
    id uuid NOT NULL,
    api_key_id uuid NOT NULL,
    scope_name character varying NOT NULL,
    created_at timestamp with time zone NOT NULL
);


--
-- Name: public_api_keys; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.public_api_keys (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    name character varying NOT NULL,
    key_hash character varying NOT NULL,
    prefix character varying(8) NOT NULL,
    is_active boolean NOT NULL,
    last_used_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL,
    status character varying NOT NULL,
    revoked_at timestamp with time zone,
    revoked_by uuid,
    request_count integer NOT NULL,
    last_ip character varying,
    last_user_agent character varying,
    rate_limit_tier character varying NOT NULL
);


--
-- Name: public_async_jobs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.public_async_jobs (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    job_type character varying NOT NULL,
    status character varying NOT NULL,
    result_payload jsonb,
    error_message text,
    created_at timestamp with time zone NOT NULL,
    completed_at timestamp with time zone,
    attempts integer DEFAULT 0 NOT NULL,
    max_attempts integer DEFAULT 5 NOT NULL,
    last_error text,
    expires_at timestamp with time zone
);


--
-- Name: public_webhooks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.public_webhooks (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    source character varying NOT NULL,
    url character varying,
    secret_hash character varying NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone NOT NULL
);


--
-- Name: router_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.router_events (
    id uuid NOT NULL,
    conversation_id uuid NOT NULL,
    primary_intent character varying(50) NOT NULL,
    secondary_intent character varying(50),
    confidence double precision NOT NULL,
    decision character varying(50) NOT NULL,
    routed_agent character varying(50),
    created_at timestamp with time zone NOT NULL
);


--
-- Name: sentiments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sentiments (
    id uuid NOT NULL,
    conversation_id uuid NOT NULL,
    score numeric(5,2) NOT NULL,
    label character varying(20) NOT NULL,
    analyzed_at timestamp with time zone NOT NULL
);


--
-- Name: tickets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tickets (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    customer_id uuid NOT NULL,
    conversation_id uuid NOT NULL,
    title character varying(255) NOT NULL,
    description text,
    priority character varying(20) DEFAULT 'medium'::character varying NOT NULL,
    status character varying(20) DEFAULT 'open'::character varying NOT NULL,
    assigned_to uuid,
    created_at timestamp with time zone NOT NULL,
    issue_type character varying(50),
    probable_cause text,
    last_troubleshooting_step text,
    escalation_reason text,
    last_interaction_at timestamp with time zone
);


--
-- Name: topic_registry; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.topic_registry (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    canonical_topic character varying(255) NOT NULL,
    display_name character varying(255) NOT NULL,
    aliases jsonb NOT NULL,
    category character varying(255),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


--
-- Name: topics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.topics (
    id uuid NOT NULL,
    conversation_id uuid NOT NULL,
    topic_name character varying(255) NOT NULL,
    confidence numeric(5,2),
    created_at timestamp with time zone NOT NULL
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id uuid NOT NULL,
    email character varying(255) NOT NULL,
    full_name character varying(255) NOT NULL,
    avatar_url text,
    password_hash text NOT NULL,
    status character varying(20) DEFAULT 'active'::character varying NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


--
-- Name: voice_interactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.voice_interactions (
    id uuid NOT NULL,
    conversation_id uuid,
    created_at timestamp with time zone NOT NULL,
    workspace_id uuid NOT NULL,
    customer_id uuid,
    idempotency_key character varying(255) NOT NULL,
    channel character varying(50) DEFAULT 'public_voice'::character varying NOT NULL,
    input_audio_ref character varying(1024),
    input_audio_sha256 character varying(64),
    input_audio_mime_type character varying(100),
    input_audio_size_bytes integer,
    input_audio_bytes bytea,
    transcript_text text,
    reply_text text,
    reply_audio_ref character varying(1024),
    reply_audio_bytes bytea,
    status character varying(50) DEFAULT 'processing'::character varying NOT NULL,
    error_code character varying(100),
    error_message text,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    artifact_created_at timestamp with time zone,
    artifact_expires_at timestamp with time zone,
    artifact_deleted_at timestamp with time zone
);


--
-- Name: workflow_runs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.workflow_runs (
    id uuid NOT NULL,
    workflow_id uuid NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    execution_log jsonb,
    executed_at timestamp with time zone NOT NULL
);


--
-- Name: workflows; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.workflows (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    name character varying(255) NOT NULL,
    trigger_type character varying(100) NOT NULL,
    status character varying(20) DEFAULT 'active'::character varying NOT NULL,
    created_at timestamp with time zone NOT NULL
);


--
-- Name: workspace_members; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.workspace_members (
    id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    user_id uuid NOT NULL,
    role character varying(50) DEFAULT 'member'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: workspaces; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.workspaces (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    industry character varying(100),
    plan character varying(50) DEFAULT 'free'::character varying NOT NULL,
    status character varying(20) DEFAULT 'active'::character varying NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: analytics_daily_rollups analytics_daily_rollups_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analytics_daily_rollups
    ADD CONSTRAINT analytics_daily_rollups_pkey PRIMARY KEY (id);


--
-- Name: analytics_events analytics_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analytics_events
    ADD CONSTRAINT analytics_events_pkey PRIMARY KEY (id);


--
-- Name: analytics_hourly_rollups analytics_hourly_rollups_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analytics_hourly_rollups
    ADD CONSTRAINT analytics_hourly_rollups_pkey PRIMARY KEY (id);


--
-- Name: analytics_outbox analytics_outbox_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analytics_outbox
    ADD CONSTRAINT analytics_outbox_pkey PRIMARY KEY (id);


--
-- Name: analytics_reports analytics_reports_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analytics_reports
    ADD CONSTRAINT analytics_reports_pkey PRIMARY KEY (id);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: business_insights business_insights_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.business_insights
    ADD CONSTRAINT business_insights_pkey PRIMARY KEY (id);


--
-- Name: business_question_audit business_question_audit_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.business_question_audit
    ADD CONSTRAINT business_question_audit_pkey PRIMARY KEY (id);


--
-- Name: business_recommendations business_recommendations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.business_recommendations
    ADD CONSTRAINT business_recommendations_pkey PRIMARY KEY (id);


--
-- Name: conversation_intelligence conversation_intelligence_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_intelligence
    ADD CONSTRAINT conversation_intelligence_pkey PRIMARY KEY (id);


--
-- Name: conversation_intents conversation_intents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_intents
    ADD CONSTRAINT conversation_intents_pkey PRIMARY KEY (id);


--
-- Name: conversation_resolutions conversation_resolutions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_resolutions
    ADD CONSTRAINT conversation_resolutions_pkey PRIMARY KEY (id);


--
-- Name: conversation_sentiments conversation_sentiments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_sentiments
    ADD CONSTRAINT conversation_sentiments_pkey PRIMARY KEY (id);


--
-- Name: conversation_summaries conversation_summaries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_summaries
    ADD CONSTRAINT conversation_summaries_pkey PRIMARY KEY (id);


--
-- Name: conversation_topics conversation_topics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_topics
    ADD CONSTRAINT conversation_topics_pkey PRIMARY KEY (id);


--
-- Name: conversations conversations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_pkey PRIMARY KEY (id);


--
-- Name: customer_care_cases customer_care_cases_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_care_cases
    ADD CONSTRAINT customer_care_cases_pkey PRIMARY KEY (id);


--
-- Name: customers customers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_pkey PRIMARY KEY (id);


--
-- Name: dataset_queries dataset_queries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dataset_queries
    ADD CONSTRAINT dataset_queries_pkey PRIMARY KEY (id);


--
-- Name: datasets datasets_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.datasets
    ADD CONSTRAINT datasets_pkey PRIMARY KEY (id);


--
-- Name: document_chunks document_chunks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_chunks
    ADD CONSTRAINT document_chunks_pkey PRIMARY KEY (id);


--
-- Name: documents documents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_pkey PRIMARY KEY (id);


--
-- Name: executive_reports executive_reports_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.executive_reports
    ADD CONSTRAINT executive_reports_pkey PRIMARY KEY (id);


--
-- Name: handoffs handoffs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.handoffs
    ADD CONSTRAINT handoffs_pkey PRIMARY KEY (id);


--
-- Name: idempotency_keys idempotency_keys_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.idempotency_keys
    ADD CONSTRAINT idempotency_keys_pkey PRIMARY KEY (id);


--
-- Name: insight_lineage insight_lineage_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.insight_lineage
    ADD CONSTRAINT insight_lineage_pkey PRIMARY KEY (id);


--
-- Name: intel_daily_intent_rollups intel_daily_intent_rollups_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.intel_daily_intent_rollups
    ADD CONSTRAINT intel_daily_intent_rollups_pkey PRIMARY KEY (id);


--
-- Name: intel_daily_resolution_rollups intel_daily_resolution_rollups_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.intel_daily_resolution_rollups
    ADD CONSTRAINT intel_daily_resolution_rollups_pkey PRIMARY KEY (id);


--
-- Name: intel_daily_sentiment_rollups intel_daily_sentiment_rollups_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.intel_daily_sentiment_rollups
    ADD CONSTRAINT intel_daily_sentiment_rollups_pkey PRIMARY KEY (id);


--
-- Name: intel_daily_topic_rollups intel_daily_topic_rollups_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.intel_daily_topic_rollups
    ADD CONSTRAINT intel_daily_topic_rollups_pkey PRIMARY KEY (id);


--
-- Name: lead_profiles lead_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lead_profiles
    ADD CONSTRAINT lead_profiles_pkey PRIMARY KEY (id);


--
-- Name: messages messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_pkey PRIMARY KEY (id);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (id);


--
-- Name: public_api_key_audit public_api_key_audit_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.public_api_key_audit
    ADD CONSTRAINT public_api_key_audit_pkey PRIMARY KEY (id);


--
-- Name: public_api_key_rotations public_api_key_rotations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.public_api_key_rotations
    ADD CONSTRAINT public_api_key_rotations_pkey PRIMARY KEY (id);


--
-- Name: public_api_key_scopes public_api_key_scopes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.public_api_key_scopes
    ADD CONSTRAINT public_api_key_scopes_pkey PRIMARY KEY (id);


--
-- Name: public_api_keys public_api_keys_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.public_api_keys
    ADD CONSTRAINT public_api_keys_pkey PRIMARY KEY (id);


--
-- Name: public_async_jobs public_async_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.public_async_jobs
    ADD CONSTRAINT public_async_jobs_pkey PRIMARY KEY (id);


--
-- Name: public_webhooks public_webhooks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.public_webhooks
    ADD CONSTRAINT public_webhooks_pkey PRIMARY KEY (id);


--
-- Name: router_events router_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.router_events
    ADD CONSTRAINT router_events_pkey PRIMARY KEY (id);


--
-- Name: sentiments sentiments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sentiments
    ADD CONSTRAINT sentiments_pkey PRIMARY KEY (id);


--
-- Name: tickets tickets_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tickets
    ADD CONSTRAINT tickets_pkey PRIMARY KEY (id);


--
-- Name: topic_registry topic_registry_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.topic_registry
    ADD CONSTRAINT topic_registry_pkey PRIMARY KEY (id);


--
-- Name: topics topics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.topics
    ADD CONSTRAINT topics_pkey PRIMARY KEY (id);


--
-- Name: voice_interactions uix_workspace_voice_idemp_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.voice_interactions
    ADD CONSTRAINT uix_workspace_voice_idemp_key UNIQUE (workspace_id, idempotency_key);


--
-- Name: handoffs uq_handoff_source_message; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.handoffs
    ADD CONSTRAINT uq_handoff_source_message UNIQUE (workspace_id, conversation_id, source_message_id);


--
-- Name: lead_profiles uq_lead_workspace_customer; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lead_profiles
    ADD CONSTRAINT uq_lead_workspace_customer UNIQUE (workspace_id, customer_id);


--
-- Name: public_api_key_scopes uq_public_api_key_scope; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.public_api_key_scopes
    ADD CONSTRAINT uq_public_api_key_scope UNIQUE (api_key_id, scope_name);


--
-- Name: conversations uq_workspace_conversation_external_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT uq_workspace_conversation_external_id UNIQUE (workspace_id, external_id);


--
-- Name: customers uq_workspace_customer_external_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT uq_workspace_customer_external_id UNIQUE (workspace_id, external_id);


--
-- Name: customers uq_workspace_customer_telegram_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT uq_workspace_customer_telegram_id UNIQUE (workspace_id, telegram_id);


--
-- Name: idempotency_keys uq_workspace_idempotency_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.idempotency_keys
    ADD CONSTRAINT uq_workspace_idempotency_key UNIQUE (workspace_id, idempotency_key);


--
-- Name: public_webhooks uq_workspace_webhook_source; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.public_webhooks
    ADD CONSTRAINT uq_workspace_webhook_source UNIQUE (workspace_id, source);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: voice_interactions voice_interactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.voice_interactions
    ADD CONSTRAINT voice_interactions_pkey PRIMARY KEY (id);


--
-- Name: workflow_runs workflow_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_runs
    ADD CONSTRAINT workflow_runs_pkey PRIMARY KEY (id);


--
-- Name: workflows workflows_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflows
    ADD CONSTRAINT workflows_pkey PRIMARY KEY (id);


--
-- Name: workspace_members workspace_members_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workspace_members
    ADD CONSTRAINT workspace_members_pkey PRIMARY KEY (id);


--
-- Name: workspaces workspaces_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workspaces
    ADD CONSTRAINT workspaces_pkey PRIMARY KEY (id);


--
-- Name: idx_audit_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_user ON public.audit_logs USING btree (user_id);


--
-- Name: idx_audit_workspace; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_workspace ON public.audit_logs USING btree (workspace_id);


--
-- Name: idx_cc_cases_unique_active; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_cc_cases_unique_active ON public.customer_care_cases USING btree (workspace_id, conversation_id) WHERE ((current_stage)::text <> ALL ((ARRAY['resolved'::character varying, 'closed'::character varying])::text[]));


--
-- Name: idx_cc_cases_workspace; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cc_cases_workspace ON public.customer_care_cases USING btree (workspace_id);


--
-- Name: idx_cc_cases_ws_complaint; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cc_cases_ws_complaint ON public.customer_care_cases USING btree (workspace_id, complaint_type);


--
-- Name: idx_cc_cases_ws_conv_stage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cc_cases_ws_conv_stage ON public.customer_care_cases USING btree (workspace_id, conversation_id, current_stage);


--
-- Name: idx_cc_cases_ws_interaction; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cc_cases_ws_interaction ON public.customer_care_cases USING btree (workspace_id, last_interaction_at);


--
-- Name: idx_chunks_document; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chunks_document ON public.document_chunks USING btree (document_id);


--
-- Name: idx_chunks_embedding; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_chunks_embedding ON public.document_chunks USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: idx_conv_intel_analyzed_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_conv_intel_analyzed_at ON public.conversation_intelligence USING btree (workspace_id, analyzed_at);


--
-- Name: idx_conv_intel_ws_conv; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_conv_intel_ws_conv ON public.conversation_intelligence USING btree (workspace_id, conversation_id);


--
-- Name: idx_conv_intent_ws_conv; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_conv_intent_ws_conv ON public.conversation_intents USING btree (workspace_id, conversation_id);


--
-- Name: idx_conv_resolution_ws_conv; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_conv_resolution_ws_conv ON public.conversation_resolutions USING btree (workspace_id, conversation_id);


--
-- Name: idx_conv_sentiment_ws_conv; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_conv_sentiment_ws_conv ON public.conversation_sentiments USING btree (workspace_id, conversation_id);


--
-- Name: idx_conv_summary_ws_conv; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_conv_summary_ws_conv ON public.conversation_summaries USING btree (workspace_id, conversation_id);


--
-- Name: idx_conv_topics_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_conv_topics_name ON public.conversation_topics USING btree (workspace_id, topic_name);


--
-- Name: idx_conv_topics_ws_conv; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_conv_topics_ws_conv ON public.conversation_topics USING btree (workspace_id, conversation_id);


--
-- Name: idx_conversations_channel; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_conversations_channel ON public.conversations USING btree (channel);


--
-- Name: idx_conversations_customer; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_conversations_customer ON public.conversations USING btree (customer_id);


--
-- Name: idx_conversations_external; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_conversations_external ON public.conversations USING btree (external_id);


--
-- Name: idx_conversations_workspace; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_conversations_workspace ON public.conversations USING btree (workspace_id);


--
-- Name: idx_customers_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_customers_email ON public.customers USING btree (email);


--
-- Name: idx_customers_external; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_customers_external ON public.customers USING btree (external_id);


--
-- Name: idx_customers_telegram; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_customers_telegram ON public.customers USING btree (telegram_id);


--
-- Name: idx_customers_workspace; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_customers_workspace ON public.customers USING btree (workspace_id);


--
-- Name: idx_dataset_queries_dataset; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_dataset_queries_dataset ON public.dataset_queries USING btree (dataset_id);


--
-- Name: idx_datasets_workspace; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_datasets_workspace ON public.datasets USING btree (workspace_id);


--
-- Name: idx_documents_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_documents_status ON public.documents USING btree (status);


--
-- Name: idx_documents_workspace; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_documents_workspace ON public.documents USING btree (workspace_id);


--
-- Name: idx_handoffs_conversation; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_handoffs_conversation ON public.handoffs USING btree (conversation_id);


--
-- Name: idx_intel_intent_rollup_ws_bucket_name; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_intel_intent_rollup_ws_bucket_name ON public.intel_daily_intent_rollups USING btree (workspace_id, time_bucket, intent_name);


--
-- Name: idx_intel_resolution_rollup_ws_bucket_name; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_intel_resolution_rollup_ws_bucket_name ON public.intel_daily_resolution_rollups USING btree (workspace_id, time_bucket, resolution_type);


--
-- Name: idx_intel_sentiment_rollup_ws_bucket_name; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_intel_sentiment_rollup_ws_bucket_name ON public.intel_daily_sentiment_rollups USING btree (workspace_id, time_bucket, sentiment);


--
-- Name: idx_intel_topic_rollup_ws_bucket_name; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_intel_topic_rollup_ws_bucket_name ON public.intel_daily_topic_rollups USING btree (workspace_id, time_bucket, topic_name);


--
-- Name: idx_leads_workspace_intent; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_leads_workspace_intent ON public.lead_profiles USING btree (workspace_id, buying_intent);


--
-- Name: idx_leads_workspace_interaction; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_leads_workspace_interaction ON public.lead_profiles USING btree (workspace_id, last_interaction_at);


--
-- Name: idx_leads_workspace_stage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_leads_workspace_stage ON public.lead_profiles USING btree (workspace_id, current_stage);


--
-- Name: idx_messages_conversation; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_messages_conversation ON public.messages USING btree (conversation_id);


--
-- Name: idx_messages_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_messages_created ON public.messages USING btree (created_at);


--
-- Name: idx_notifications_read; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_notifications_read ON public.notifications USING btree (is_read);


--
-- Name: idx_notifications_workspace; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_notifications_workspace ON public.notifications USING btree (workspace_id);


--
-- Name: idx_reports_workspace; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_reports_workspace ON public.analytics_reports USING btree (workspace_id);


--
-- Name: idx_router_events_conversation; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_router_events_conversation ON public.router_events USING btree (conversation_id);


--
-- Name: idx_sentiments_label; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sentiments_label ON public.sentiments USING btree (label);


--
-- Name: idx_tickets_priority; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tickets_priority ON public.tickets USING btree (priority);


--
-- Name: idx_tickets_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tickets_status ON public.tickets USING btree (status);


--
-- Name: idx_tickets_workspace; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tickets_workspace ON public.tickets USING btree (workspace_id);


--
-- Name: idx_tickets_ws_conv_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tickets_ws_conv_status ON public.tickets USING btree (workspace_id, conversation_id, status);


--
-- Name: idx_tickets_ws_issue; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tickets_ws_issue ON public.tickets USING btree (workspace_id, issue_type);


--
-- Name: idx_tickets_ws_last_interaction; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_tickets_ws_last_interaction ON public.tickets USING btree (workspace_id, last_interaction_at);


--
-- Name: idx_topic_registry_canonical; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_topic_registry_canonical ON public.topic_registry USING btree (workspace_id, canonical_topic);


--
-- Name: idx_topics_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_topics_name ON public.topics USING btree (topic_name);


--
-- Name: idx_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_email ON public.users USING btree (email);


--
-- Name: idx_voice_conversation; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_voice_conversation ON public.voice_interactions USING btree (conversation_id);


--
-- Name: idx_voice_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_voice_created_at ON public.voice_interactions USING btree (created_at);


--
-- Name: idx_voice_workspace; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_voice_workspace ON public.voice_interactions USING btree (workspace_id);


--
-- Name: idx_workflow_runs_workflow; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflow_runs_workflow ON public.workflow_runs USING btree (workflow_id);


--
-- Name: idx_workflows_workspace; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workflows_workspace ON public.workflows USING btree (workspace_id);


--
-- Name: idx_workspaces_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_workspaces_status ON public.workspaces USING btree (status);


--
-- Name: idx_wsmember_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_wsmember_user ON public.workspace_members USING btree (user_id);


--
-- Name: idx_wsmember_workspace; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_wsmember_workspace ON public.workspace_members USING btree (workspace_id);


--
-- Name: idx_wsmember_workspace_user; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_wsmember_workspace_user ON public.workspace_members USING btree (workspace_id, user_id);


--
-- Name: ix_analytics_daily_rollups_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_analytics_daily_rollups_id ON public.analytics_daily_rollups USING btree (id);


--
-- Name: ix_analytics_daily_rollups_metric_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_analytics_daily_rollups_metric_name ON public.analytics_daily_rollups USING btree (metric_name);


--
-- Name: ix_analytics_daily_rollups_time_bucket; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_analytics_daily_rollups_time_bucket ON public.analytics_daily_rollups USING btree (time_bucket);


--
-- Name: ix_analytics_daily_rollups_workspace_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_analytics_daily_rollups_workspace_id ON public.analytics_daily_rollups USING btree (workspace_id);


--
-- Name: ix_analytics_events_conversation_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_analytics_events_conversation_id ON public.analytics_events USING btree (conversation_id);


--
-- Name: ix_analytics_events_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_analytics_events_created_at ON public.analytics_events USING btree (created_at);


--
-- Name: ix_analytics_events_customer_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_analytics_events_customer_id ON public.analytics_events USING btree (customer_id);


--
-- Name: ix_analytics_events_event_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_analytics_events_event_type ON public.analytics_events USING btree (event_type);


--
-- Name: ix_analytics_events_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_analytics_events_id ON public.analytics_events USING btree (id);


--
-- Name: ix_analytics_events_idempotency_key; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_analytics_events_idempotency_key ON public.analytics_events USING btree (idempotency_key);


--
-- Name: ix_analytics_events_workspace_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_analytics_events_workspace_id ON public.analytics_events USING btree (workspace_id);


--
-- Name: ix_analytics_events_ws_type_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_analytics_events_ws_type_date ON public.analytics_events USING btree (workspace_id, event_type, created_at);


--
-- Name: ix_analytics_hourly_rollups_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_analytics_hourly_rollups_id ON public.analytics_hourly_rollups USING btree (id);


--
-- Name: ix_analytics_hourly_rollups_metric_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_analytics_hourly_rollups_metric_name ON public.analytics_hourly_rollups USING btree (metric_name);


--
-- Name: ix_analytics_hourly_rollups_time_bucket; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_analytics_hourly_rollups_time_bucket ON public.analytics_hourly_rollups USING btree (time_bucket);


--
-- Name: ix_analytics_hourly_rollups_workspace_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_analytics_hourly_rollups_workspace_id ON public.analytics_hourly_rollups USING btree (workspace_id);


--
-- Name: ix_analytics_outbox_idempotency_key; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_analytics_outbox_idempotency_key ON public.analytics_outbox USING btree (idempotency_key);


--
-- Name: ix_business_insight_fingerprint; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_business_insight_fingerprint ON public.business_insights USING btree (workspace_id, fingerprint);


--
-- Name: ix_business_insight_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_business_insight_status ON public.business_insights USING btree (status);


--
-- Name: ix_business_insight_workspace; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_business_insight_workspace ON public.business_insights USING btree (workspace_id);


--
-- Name: ix_business_rec_insight; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_business_rec_insight ON public.business_recommendations USING btree (insight_id);


--
-- Name: ix_business_rec_workspace; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_business_rec_workspace ON public.business_recommendations USING btree (workspace_id);


--
-- Name: ix_dr_ws_bucket_metric; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_dr_ws_bucket_metric ON public.analytics_daily_rollups USING btree (workspace_id, time_bucket, metric_name);


--
-- Name: ix_executive_report_fingerprint; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_executive_report_fingerprint ON public.executive_reports USING btree (workspace_id, fingerprint);


--
-- Name: ix_executive_report_workspace; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_executive_report_workspace ON public.executive_reports USING btree (workspace_id);


--
-- Name: ix_hr_ws_bucket_metric; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_hr_ws_bucket_metric ON public.analytics_hourly_rollups USING btree (workspace_id, time_bucket, metric_name);


--
-- Name: ix_idempotency_keys_expires_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_idempotency_keys_expires_at ON public.idempotency_keys USING btree (expires_at);


--
-- Name: ix_insight_lineage_insight_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_insight_lineage_insight_id ON public.insight_lineage USING btree (insight_id);


--
-- Name: ix_outbox_status_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_outbox_status_created ON public.analytics_outbox USING btree (status, created_at);


--
-- Name: ix_public_api_key_audit_api_key_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_public_api_key_audit_api_key_id ON public.public_api_key_audit USING btree (api_key_id);


--
-- Name: ix_public_api_key_audit_workspace_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_public_api_key_audit_workspace_id ON public.public_api_key_audit USING btree (workspace_id);


--
-- Name: ix_public_api_key_rotations_api_key_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_public_api_key_rotations_api_key_id ON public.public_api_key_rotations USING btree (api_key_id);


--
-- Name: ix_public_api_key_rotations_workspace_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_public_api_key_rotations_workspace_id ON public.public_api_key_rotations USING btree (workspace_id);


--
-- Name: ix_public_api_key_scopes_key_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_public_api_key_scopes_key_id ON public.public_api_key_scopes USING btree (api_key_id);


--
-- Name: ix_public_api_keys_prefix; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_public_api_keys_prefix ON public.public_api_keys USING btree (prefix);


--
-- Name: ix_public_api_keys_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_public_api_keys_status ON public.public_api_keys USING btree (status);


--
-- Name: ix_public_api_keys_workspace_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_public_api_keys_workspace_id ON public.public_api_keys USING btree (workspace_id);


--
-- Name: ix_public_async_jobs_status_attempts; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_public_async_jobs_status_attempts ON public.public_async_jobs USING btree (status, attempts);


--
-- Name: ix_public_async_jobs_workspace_id_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_public_async_jobs_workspace_id_status ON public.public_async_jobs USING btree (workspace_id, status);


--
-- Name: ix_question_audit_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_question_audit_created_at ON public.business_question_audit USING btree (created_at);


--
-- Name: ix_question_audit_workspace; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_question_audit_workspace ON public.business_question_audit USING btree (workspace_id);


--
-- Name: analytics_daily_rollups analytics_daily_rollups_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analytics_daily_rollups
    ADD CONSTRAINT analytics_daily_rollups_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: analytics_events analytics_events_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analytics_events
    ADD CONSTRAINT analytics_events_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: analytics_hourly_rollups analytics_hourly_rollups_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analytics_hourly_rollups
    ADD CONSTRAINT analytics_hourly_rollups_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: analytics_outbox analytics_outbox_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analytics_outbox
    ADD CONSTRAINT analytics_outbox_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: analytics_reports analytics_reports_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analytics_reports
    ADD CONSTRAINT analytics_reports_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: audit_logs audit_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: audit_logs audit_logs_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: business_insights business_insights_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.business_insights
    ADD CONSTRAINT business_insights_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: business_question_audit business_question_audit_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.business_question_audit
    ADD CONSTRAINT business_question_audit_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: business_recommendations business_recommendations_insight_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.business_recommendations
    ADD CONSTRAINT business_recommendations_insight_id_fkey FOREIGN KEY (insight_id) REFERENCES public.business_insights(id) ON DELETE CASCADE;


--
-- Name: business_recommendations business_recommendations_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.business_recommendations
    ADD CONSTRAINT business_recommendations_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: conversation_intelligence conversation_intelligence_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_intelligence
    ADD CONSTRAINT conversation_intelligence_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;


--
-- Name: conversation_intelligence conversation_intelligence_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_intelligence
    ADD CONSTRAINT conversation_intelligence_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: conversation_intents conversation_intents_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_intents
    ADD CONSTRAINT conversation_intents_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;


--
-- Name: conversation_intents conversation_intents_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_intents
    ADD CONSTRAINT conversation_intents_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: conversation_resolutions conversation_resolutions_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_resolutions
    ADD CONSTRAINT conversation_resolutions_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;


--
-- Name: conversation_resolutions conversation_resolutions_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_resolutions
    ADD CONSTRAINT conversation_resolutions_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: conversation_sentiments conversation_sentiments_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_sentiments
    ADD CONSTRAINT conversation_sentiments_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;


--
-- Name: conversation_sentiments conversation_sentiments_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_sentiments
    ADD CONSTRAINT conversation_sentiments_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: conversation_summaries conversation_summaries_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_summaries
    ADD CONSTRAINT conversation_summaries_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;


--
-- Name: conversation_summaries conversation_summaries_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_summaries
    ADD CONSTRAINT conversation_summaries_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: conversation_topics conversation_topics_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_topics
    ADD CONSTRAINT conversation_topics_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;


--
-- Name: conversation_topics conversation_topics_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_topics
    ADD CONSTRAINT conversation_topics_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: conversations conversations_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(id) ON DELETE CASCADE;


--
-- Name: conversations conversations_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: customer_care_cases customer_care_cases_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_care_cases
    ADD CONSTRAINT customer_care_cases_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;


--
-- Name: customer_care_cases customer_care_cases_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_care_cases
    ADD CONSTRAINT customer_care_cases_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(id) ON DELETE CASCADE;


--
-- Name: customer_care_cases customer_care_cases_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_care_cases
    ADD CONSTRAINT customer_care_cases_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: customers customers_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: dataset_queries dataset_queries_dataset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dataset_queries
    ADD CONSTRAINT dataset_queries_dataset_id_fkey FOREIGN KEY (dataset_id) REFERENCES public.datasets(id) ON DELETE CASCADE;


--
-- Name: datasets datasets_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.datasets
    ADD CONSTRAINT datasets_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: document_chunks document_chunks_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_chunks
    ADD CONSTRAINT document_chunks_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE;


--
-- Name: documents documents_uploaded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_uploaded_by_fkey FOREIGN KEY (uploaded_by) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: documents documents_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: executive_reports executive_reports_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.executive_reports
    ADD CONSTRAINT executive_reports_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: customer_care_cases fk_cc_parent_case_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customer_care_cases
    ADD CONSTRAINT fk_cc_parent_case_id FOREIGN KEY (parent_case_id) REFERENCES public.customer_care_cases(id) ON DELETE SET NULL;


--
-- Name: handoffs fk_handoffs_workspace_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.handoffs
    ADD CONSTRAINT fk_handoffs_workspace_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: voice_interactions fk_voice_customer_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.voice_interactions
    ADD CONSTRAINT fk_voice_customer_id FOREIGN KEY (customer_id) REFERENCES public.customers(id) ON DELETE SET NULL;


--
-- Name: voice_interactions fk_voice_workspace_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.voice_interactions
    ADD CONSTRAINT fk_voice_workspace_id FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: handoffs handoffs_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.handoffs
    ADD CONSTRAINT handoffs_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;


--
-- Name: idempotency_keys idempotency_keys_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.idempotency_keys
    ADD CONSTRAINT idempotency_keys_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: insight_lineage insight_lineage_insight_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.insight_lineage
    ADD CONSTRAINT insight_lineage_insight_id_fkey FOREIGN KEY (insight_id) REFERENCES public.business_insights(id) ON DELETE CASCADE;


--
-- Name: intel_daily_intent_rollups intel_daily_intent_rollups_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.intel_daily_intent_rollups
    ADD CONSTRAINT intel_daily_intent_rollups_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: intel_daily_resolution_rollups intel_daily_resolution_rollups_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.intel_daily_resolution_rollups
    ADD CONSTRAINT intel_daily_resolution_rollups_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: intel_daily_sentiment_rollups intel_daily_sentiment_rollups_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.intel_daily_sentiment_rollups
    ADD CONSTRAINT intel_daily_sentiment_rollups_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: intel_daily_topic_rollups intel_daily_topic_rollups_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.intel_daily_topic_rollups
    ADD CONSTRAINT intel_daily_topic_rollups_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: lead_profiles lead_profiles_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lead_profiles
    ADD CONSTRAINT lead_profiles_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(id) ON DELETE CASCADE;


--
-- Name: lead_profiles lead_profiles_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lead_profiles
    ADD CONSTRAINT lead_profiles_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: messages messages_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;


--
-- Name: notifications notifications_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: public_api_key_audit public_api_key_audit_actor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.public_api_key_audit
    ADD CONSTRAINT public_api_key_audit_actor_id_fkey FOREIGN KEY (actor_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: public_api_key_audit public_api_key_audit_api_key_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.public_api_key_audit
    ADD CONSTRAINT public_api_key_audit_api_key_id_fkey FOREIGN KEY (api_key_id) REFERENCES public.public_api_keys(id) ON DELETE CASCADE;


--
-- Name: public_api_key_audit public_api_key_audit_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.public_api_key_audit
    ADD CONSTRAINT public_api_key_audit_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: public_api_key_rotations public_api_key_rotations_api_key_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.public_api_key_rotations
    ADD CONSTRAINT public_api_key_rotations_api_key_id_fkey FOREIGN KEY (api_key_id) REFERENCES public.public_api_keys(id) ON DELETE CASCADE;


--
-- Name: public_api_key_rotations public_api_key_rotations_rotated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.public_api_key_rotations
    ADD CONSTRAINT public_api_key_rotations_rotated_by_fkey FOREIGN KEY (rotated_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: public_api_key_rotations public_api_key_rotations_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.public_api_key_rotations
    ADD CONSTRAINT public_api_key_rotations_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: public_api_key_scopes public_api_key_scopes_api_key_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.public_api_key_scopes
    ADD CONSTRAINT public_api_key_scopes_api_key_id_fkey FOREIGN KEY (api_key_id) REFERENCES public.public_api_keys(id) ON DELETE CASCADE;


--
-- Name: public_api_keys public_api_keys_revoked_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.public_api_keys
    ADD CONSTRAINT public_api_keys_revoked_by_fkey FOREIGN KEY (revoked_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: public_api_keys public_api_keys_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.public_api_keys
    ADD CONSTRAINT public_api_keys_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: public_async_jobs public_async_jobs_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.public_async_jobs
    ADD CONSTRAINT public_async_jobs_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: public_webhooks public_webhooks_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.public_webhooks
    ADD CONSTRAINT public_webhooks_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: router_events router_events_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.router_events
    ADD CONSTRAINT router_events_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;


--
-- Name: sentiments sentiments_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sentiments
    ADD CONSTRAINT sentiments_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;


--
-- Name: tickets tickets_assigned_to_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tickets
    ADD CONSTRAINT tickets_assigned_to_fkey FOREIGN KEY (assigned_to) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: tickets tickets_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tickets
    ADD CONSTRAINT tickets_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;


--
-- Name: tickets tickets_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tickets
    ADD CONSTRAINT tickets_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(id) ON DELETE CASCADE;


--
-- Name: tickets tickets_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tickets
    ADD CONSTRAINT tickets_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: topic_registry topic_registry_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.topic_registry
    ADD CONSTRAINT topic_registry_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: topics topics_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.topics
    ADD CONSTRAINT topics_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;


--
-- Name: voice_interactions voice_interactions_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.voice_interactions
    ADD CONSTRAINT voice_interactions_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE SET NULL;


--
-- Name: workflow_runs workflow_runs_workflow_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflow_runs
    ADD CONSTRAINT workflow_runs_workflow_id_fkey FOREIGN KEY (workflow_id) REFERENCES public.workflows(id) ON DELETE CASCADE;


--
-- Name: workflows workflows_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workflows
    ADD CONSTRAINT workflows_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: workspace_members workspace_members_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workspace_members
    ADD CONSTRAINT workspace_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: workspace_members workspace_members_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workspace_members
    ADD CONSTRAINT workspace_members_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;


--
-- Name: alembic_version; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.alembic_version ENABLE ROW LEVEL SECURITY;

--
-- Name: analytics_daily_rollups; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.analytics_daily_rollups ENABLE ROW LEVEL SECURITY;

--
-- Name: analytics_events; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.analytics_events ENABLE ROW LEVEL SECURITY;

--
-- Name: analytics_hourly_rollups; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.analytics_hourly_rollups ENABLE ROW LEVEL SECURITY;

--
-- Name: analytics_outbox; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.analytics_outbox ENABLE ROW LEVEL SECURITY;

--
-- Name: analytics_reports; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.analytics_reports ENABLE ROW LEVEL SECURITY;

--
-- Name: audit_logs; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

--
-- Name: business_insights; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.business_insights ENABLE ROW LEVEL SECURITY;

--
-- Name: business_question_audit; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.business_question_audit ENABLE ROW LEVEL SECURITY;

--
-- Name: business_recommendations; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.business_recommendations ENABLE ROW LEVEL SECURITY;

--
-- Name: conversation_intelligence; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.conversation_intelligence ENABLE ROW LEVEL SECURITY;

--
-- Name: conversation_intents; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.conversation_intents ENABLE ROW LEVEL SECURITY;

--
-- Name: conversation_resolutions; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.conversation_resolutions ENABLE ROW LEVEL SECURITY;

--
-- Name: conversation_sentiments; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.conversation_sentiments ENABLE ROW LEVEL SECURITY;

--
-- Name: conversation_summaries; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.conversation_summaries ENABLE ROW LEVEL SECURITY;

--
-- Name: conversation_topics; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.conversation_topics ENABLE ROW LEVEL SECURITY;

--
-- Name: conversations; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;

--
-- Name: customer_care_cases; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.customer_care_cases ENABLE ROW LEVEL SECURITY;

--
-- Name: customers; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.customers ENABLE ROW LEVEL SECURITY;

--
-- Name: dataset_queries; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.dataset_queries ENABLE ROW LEVEL SECURITY;

--
-- Name: datasets; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.datasets ENABLE ROW LEVEL SECURITY;

--
-- Name: document_chunks; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.document_chunks ENABLE ROW LEVEL SECURITY;

--
-- Name: document_chunks_backup_20_6_5; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.document_chunks_backup_20_6_5 ENABLE ROW LEVEL SECURITY;

--
-- Name: documents; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;

--
-- Name: documents_backup_20_6_5; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.documents_backup_20_6_5 ENABLE ROW LEVEL SECURITY;

--
-- Name: executive_reports; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.executive_reports ENABLE ROW LEVEL SECURITY;

--
-- Name: handoffs; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.handoffs ENABLE ROW LEVEL SECURITY;

--
-- Name: idempotency_keys; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.idempotency_keys ENABLE ROW LEVEL SECURITY;

--
-- Name: insight_lineage; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.insight_lineage ENABLE ROW LEVEL SECURITY;

--
-- Name: intel_daily_intent_rollups; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.intel_daily_intent_rollups ENABLE ROW LEVEL SECURITY;

--
-- Name: intel_daily_resolution_rollups; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.intel_daily_resolution_rollups ENABLE ROW LEVEL SECURITY;

--
-- Name: intel_daily_sentiment_rollups; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.intel_daily_sentiment_rollups ENABLE ROW LEVEL SECURITY;

--
-- Name: intel_daily_topic_rollups; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.intel_daily_topic_rollups ENABLE ROW LEVEL SECURITY;

--
-- Name: lead_profiles; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.lead_profiles ENABLE ROW LEVEL SECURITY;

--
-- Name: messages; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

--
-- Name: notifications; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;

--
-- Name: public_api_key_audit; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.public_api_key_audit ENABLE ROW LEVEL SECURITY;

--
-- Name: public_api_key_rotations; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.public_api_key_rotations ENABLE ROW LEVEL SECURITY;

--
-- Name: public_api_key_scopes; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.public_api_key_scopes ENABLE ROW LEVEL SECURITY;

--
-- Name: public_api_keys; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.public_api_keys ENABLE ROW LEVEL SECURITY;

--
-- Name: public_async_jobs; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.public_async_jobs ENABLE ROW LEVEL SECURITY;

--
-- Name: public_webhooks; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.public_webhooks ENABLE ROW LEVEL SECURITY;

--
-- Name: router_events; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.router_events ENABLE ROW LEVEL SECURITY;

--
-- Name: sentiments; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.sentiments ENABLE ROW LEVEL SECURITY;

--
-- Name: tickets; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.tickets ENABLE ROW LEVEL SECURITY;

--
-- Name: topic_registry; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.topic_registry ENABLE ROW LEVEL SECURITY;

--
-- Name: topics; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.topics ENABLE ROW LEVEL SECURITY;

--
-- Name: users; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

--
-- Name: voice_interactions; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.voice_interactions ENABLE ROW LEVEL SECURITY;

--
-- Name: workflow_runs; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.workflow_runs ENABLE ROW LEVEL SECURITY;

--
-- Name: workflows; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.workflows ENABLE ROW LEVEL SECURITY;

--
-- Name: workspace_members; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.workspace_members ENABLE ROW LEVEL SECURITY;

--
-- Name: workspaces; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.workspaces ENABLE ROW LEVEL SECURITY;

--
-- PostgreSQL database dump complete
--

\unrestrict OBBsz3urdeIzpCT0hZ8xvVHmVG1DLkECDaHlrfqsD16vtRXKgKfDth1RMQKG5m4

