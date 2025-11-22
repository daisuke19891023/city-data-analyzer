-- Migration: update insight_feedback schema and add program_version to analysis queries
ALTER TABLE analysis_queries ADD COLUMN program_version VARCHAR(100);

DROP TABLE IF EXISTS insight_feedback;
CREATE TABLE IF NOT EXISTS insight_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER REFERENCES insight_candidates(id),
    analysis_id INTEGER REFERENCES analysis_queries(id),
    rating INTEGER NOT NULL,
    comment TEXT,
    target_module VARCHAR(100) NOT NULL,
    created_at DATETIME NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_feedback_candidate_id ON insight_feedback(candidate_id);
CREATE INDEX IF NOT EXISTS idx_feedback_analysis_id ON insight_feedback(analysis_id);
