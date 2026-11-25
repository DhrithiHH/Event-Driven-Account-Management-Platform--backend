-- ==============================================================================
-- Event-Driven Account Management Platform - Complete PostgreSQL Schema
-- Compatible with PostgreSQL 13+ and Aiven for PostgreSQL
-- ==============================================================================

-- 1. Enable UUID Extension (required for gen_random_uuid())
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. Create Users Table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL,
    password TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Index for unique email lookups
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email);
CREATE INDEX IF NOT EXISTS ix_users_id ON users (id);

-- 3. Create Custom ENUM Types for Notification Events
DO '
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = ''notification_event_type'') THEN
        CREATE TYPE notification_event_type AS ENUM (
            ''ACCOUNT_CREATED'',
            ''ACCOUNT_UPDATED'',
            ''ACCOUNT_DELETED''
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = ''notification_event_status'') THEN
        CREATE TYPE notification_event_status AS ENUM (
            ''PENDING'',
            ''PROCESSING'',
            ''SENT'',
            ''FAILED''
        );
    END IF;
END;
';

-- 4. Create Notification Events Table
CREATE TABLE IF NOT EXISTS notification_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    event_type notification_event_type NOT NULL,
    recipient VARCHAR(250) NOT NULL,
    status notification_event_status NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NULL
);

-- Indexes for performance and sorting
CREATE INDEX IF NOT EXISTS ix_notification_events_id ON notification_events (id);
CREATE INDEX IF NOT EXISTS ix_notification_events_user_id ON notification_events (user_id);
CREATE INDEX IF NOT EXISTS ix_notification_events_created_at ON notification_events (created_at DESC);

-- 5. Mark Alembic Migration Version (So alembic recognizes the schema as up-to-date)
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

DELETE FROM alembic_version;
INSERT INTO alembic_version (version_num) VALUES ('c4d8e9f0a1b2');
