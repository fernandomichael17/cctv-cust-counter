CREATE TABLE IF NOT EXISTS count_events (
  id BIGSERIAL PRIMARY KEY,
  camera_id TEXT NOT NULL,
  direction TEXT NOT NULL CHECK(direction IN ('IN','OUT')),
  observed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_events_time ON count_events(observed_at);
CREATE INDEX IF NOT EXISTS idx_events_camera_time ON count_events(camera_id, observed_at);
CREATE TABLE IF NOT EXISTS camera_status (
  camera_id TEXT PRIMARY KEY,
  status TEXT NOT NULL,
  last_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  detail TEXT
);
