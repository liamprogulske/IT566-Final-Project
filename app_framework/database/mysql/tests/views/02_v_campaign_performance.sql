USE it566_project_db;

CREATE OR REPLACE VIEW v_campaign_performance AS
SELECT
  c.campaign_id,
  c.name AS campaign_name,
  c.status,
  SUM(m.impressions)       AS total_impressions,
  SUM(m.clicks)            AS total_clicks,
  SUM(m.cost_cents)        AS total_cost_cents,
  (SUM(m.cost_cents) / 100.0) AS total_cost_usd,
  CASE
    WHEN SUM(m.impressions) > 0 THEN
      ROUND(SUM(m.clicks) / SUM(m.impressions) * 100, 2)
    ELSE NULL
  END AS ctr_pct,
  CASE
    WHEN SUM(m.clicks) > 0 THEN
      ROUND(SUM(m.cost_cents) / SUM(m.clicks) / 100.0, 2)
    ELSE NULL
  END AS cpc_usd
FROM campaign c
LEFT JOIN campaign_daily_metrics m
  ON c.campaign_id = m.campaign_id
GROUP BY c.campaign_id, c.name, c.status;
