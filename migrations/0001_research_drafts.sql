CREATE TABLE IF NOT EXISTS research_drafts (
  id TEXT PRIMARY KEY,
  status TEXT NOT NULL CHECK (status IN ('pending', 'approved', 'rejected')),
  generated_at TEXT NOT NULL,
  model TEXT NOT NULL,
  focus TEXT NOT NULL,
  market_context TEXT NOT NULL DEFAULT '',
  research_json TEXT NOT NULL,
  sources_json TEXT NOT NULL,
  reviewed_at TEXT,
  reviewer_note TEXT,
  published_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_research_drafts_status_generated
  ON research_drafts(status, generated_at DESC);
