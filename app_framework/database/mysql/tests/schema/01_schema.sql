-- ============================================================
-- 01_schema.sql
-- Core schema for it566_project_db
-- Tables:
--   - channel
--   - campaign
--   - campaign_channel_xref
--   - campaign_daily_metrics
-- ============================================================

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS campaign_daily_metrics;
DROP TABLE IF EXISTS campaign_channel_xref;
DROP TABLE IF EXISTS campaign;
DROP TABLE IF EXISTS channel;

SET FOREIGN_KEY_CHECKS = 1;

-- -------------------------
-- CHANNEL
-- -------------------------
CREATE TABLE channel (
  channel_id   INT NOT NULL AUTO_INCREMENT,
  name         VARCHAR(255) NOT NULL,
  type         VARCHAR(50)  NOT NULL DEFAULT 'Other',
  created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (channel_id),
  UNIQUE KEY uq_channel_name (name)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

-- -------------------------
-- CAMPAIGN
-- -------------------------
CREATE TABLE campaign (
  campaign_id  INT NOT NULL AUTO_INCREMENT,
  name         VARCHAR(255) NOT NULL,
  start_date   DATE,
  end_date     DATE,
  status       ENUM('draft','active','paused','archived')
                 NOT NULL DEFAULT 'draft',
  budget_cents BIGINT NOT NULL DEFAULT 0,
  created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (campaign_id),
  KEY idx_campaign_name (name)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

-- -------------------------
-- CAMPAIGN ↔ CHANNEL XREF
-- -------------------------
CREATE TABLE campaign_channel_xref (
  campaign_id INT NOT NULL,
  channel_id  INT NOT NULL,
  PRIMARY KEY (campaign_id, channel_id),
  KEY fk_ccx_channel (channel_id),
  CONSTRAINT fk_ccx_campaign
    FOREIGN KEY (campaign_id)
    REFERENCES campaign (campaign_id)
    ON DELETE CASCADE,
  CONSTRAINT fk_ccx_channel
    FOREIGN KEY (channel_id)
    REFERENCES channel (channel_id)
    ON DELETE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

-- -------------------------
-- CAMPAIGN DAILY METRICS
-- -------------------------
CREATE TABLE campaign_daily_metrics (
  campaign_id   INT NOT NULL,
  metric_date   DATE NOT NULL,
  impressions   INT DEFAULT 0,
  clicks        INT DEFAULT 0,
  spend_cents   BIGINT DEFAULT 0,
  revenue_cents BIGINT DEFAULT 0,
  PRIMARY KEY (campaign_id, metric_date),
  CONSTRAINT fk_campaign_daily_metrics_campaign
    FOREIGN KEY (campaign_id)
    REFERENCES campaign (campaign_id)
    ON DELETE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;
