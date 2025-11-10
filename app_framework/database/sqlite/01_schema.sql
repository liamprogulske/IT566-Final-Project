
-- 01_schema.sql (SQLite)
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS channel (
  channel_id   INTEGER PRIMARY KEY AUTOINCREMENT,
  name         TEXT NOT NULL UNIQUE,
  type         TEXT NOT NULL CHECK(type IN ('search','social','display','email','other')),
  created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS campaign (
  campaign_id  INTEGER PRIMARY KEY AUTOINCREMENT,
  name         TEXT NOT NULL,
  start_date   TEXT,
  end_date     TEXT,
  status       TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','active','paused','archived')),
  budget_cents INTEGER NOT NULL DEFAULT 0,
  created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS campaign_channel_xref (
  campaign_id  INTEGER NOT NULL,
  channel_id   INTEGER NOT NULL,
  PRIMARY KEY (campaign_id, channel_id),
  FOREIGN KEY (campaign_id) REFERENCES campaign(campaign_id) ON DELETE CASCADE,
  FOREIGN KEY (channel_id)  REFERENCES channel(channel_id)  ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_campaign_name ON campaign(name);
CREATE INDEX IF NOT EXISTS idx_channel_name  ON channel(name);
