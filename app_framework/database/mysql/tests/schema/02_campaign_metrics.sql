USE it566_project_db;

CREATE TABLE IF NOT EXISTS campaign_daily_metrics (
  campaign_id   INT         NOT NULL,
  metric_date   DATE        NOT NULL,
  impressions   INT UNSIGNED NOT NULL DEFAULT 0,
  clicks        INT UNSIGNED NOT NULL DEFAULT 0,
  cost_cents    INT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (campaign_id, metric_date),
  CONSTRAINT fk_metrics_campaign
    FOREIGN KEY (campaign_id)
    REFERENCES campaign(campaign_id)
    ON DELETE CASCADE
) ENGINE=InnoDB;
