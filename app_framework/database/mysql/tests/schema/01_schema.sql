-- Active: 1764874923091@@localhost@3306@it566_project_db

-- 01_schema.sql (MySQL)
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS=0;

CREATE DATABASE IF NOT EXISTS it566_project_db
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;
USE it566_project_db;

CREATE TABLE IF NOT EXISTS channel (
  channel_id   INT AUTO_INCREMENT PRIMARY KEY,
  name         VARCHAR(255) NOT NULL UNIQUE,
  type         ENUM('search','social','display','email','other') NOT NULL,
  created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS campaign (
  campaign_id  INT AUTO_INCREMENT PRIMARY KEY,
  name         VARCHAR(255) NOT NULL,
  start_date   DATE NULL,
  end_date     DATE NULL,
  status       ENUM('draft','active','paused','archived') NOT NULL DEFAULT 'draft',
  budget_cents BIGINT NOT NULL DEFAULT 0,
  created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_campaign_name (name)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS campaign_channel_xref (
  campaign_id  INT NOT NULL,
  channel_id   INT NOT NULL,
  PRIMARY KEY (campaign_id, channel_id),
  CONSTRAINT fk_ccx_campaign FOREIGN KEY (campaign_id)
    REFERENCES campaign(campaign_id) ON DELETE CASCADE,
  CONSTRAINT fk_ccx_channel FOREIGN KEY (channel_id)
    REFERENCES channel(channel_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Daily metrics aggregated per campaign
CREATE TABLE campaign_daily_metrics (
  campaign_id     INT UNSIGNED NOT NULL,
  metric_date     DATE NOT NULL,
  impressions     INT UNSIGNED DEFAULT 0,
  clicks          INT UNSIGNED DEFAULT 0,
  spend_cents BIGINT UNSIGNED DEFAULT 0,
  revenue_cents BIGINT UNSIGNED DEFAULT 0,
  PRIMARY KEY (campaign_id, metric_date),
  CONSTRAINT fk_campaign_daily_metrics_campaign
    FOREIGN KEY (campaign_id)
    REFERENCES campaign(campaign_id)
    ON DELETE CASCADE
);

SET FOREIGN_KEY_CHECKS=1;
