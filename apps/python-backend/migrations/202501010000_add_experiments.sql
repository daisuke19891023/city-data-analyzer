-- Migration: add experiments, experiment_jobs, insight_candidates, insight_feedback
CREATE TABLE IF NOT EXISTS experiments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_description TEXT NOT NULL,
    dataset_ids JSON NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS experiment_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id INTEGER NOT NULL REFERENCES experiments(id),
    dataset_id INTEGER NOT NULL,
    job_type VARCHAR(100) NOT NULL,
    description TEXT,
    query_spec JSON NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    error_message TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    started_at DATETIME,
    completed_at DATETIME
);

CREATE TABLE IF NOT EXISTS insight_candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id INTEGER NOT NULL REFERENCES experiments(id),
    job_id INTEGER REFERENCES experiment_jobs(id),
    dataset_id INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    metrics JSON,
    adopted BOOLEAN NOT NULL DEFAULT 0,
    feedback_comment TEXT,
    created_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS insight_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER NOT NULL REFERENCES insight_candidates(id),
    decision VARCHAR(50) NOT NULL,
    comment TEXT,
    created_at DATETIME NOT NULL
);
