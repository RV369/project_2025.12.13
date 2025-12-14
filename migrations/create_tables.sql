-- migrations/create_tables.sql

CREATE TABLE IF NOT EXISTS videos (
    id UUID PRIMARY KEY,
    creator_id UUID NOT NULL,
    video_created_at TIMESTAMPTZ NOT NULL,
    views_count BIGINT NOT NULL,
    likes_count BIGINT NOT NULL,
    comments_count BIGINT NOT NULL,
    reports_count BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS video_snapshots (
    id UUID PRIMARY KEY,
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    views_count BIGINT NOT NULL,
    likes_count BIGINT NOT NULL,
    comments_count BIGINT NOT NULL,
    reports_count BIGINT NOT NULL,
    delta_views_count BIGINT NOT NULL,
    delta_likes_count BIGINT NOT NULL,
    delta_comments_count BIGINT NOT NULL,
    delta_reports_count BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX ON video_snapshots (video_id);
CREATE INDEX ON video_snapshots (created_at);
CREATE INDEX ON videos (creator_id);
CREATE INDEX ON videos (video_created_at);
