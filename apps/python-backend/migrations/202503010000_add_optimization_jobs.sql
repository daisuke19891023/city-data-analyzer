-- Migration: add optimization_jobs queue for DSPy compilation
BEGIN;
CREATE TABLE IF NOT EXISTS optimization_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trainset_path TEXT NOT NULL,
    version TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    metric JSON,
    artifact_id INTEGER REFERENCES compiled_program_artifacts(id),
    error_message TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    started_at DATETIME,
    completed_at DATETIME
);
CREATE INDEX IF NOT EXISTS idx_optimization_jobs_status ON optimization_jobs(status);
COMMIT;
