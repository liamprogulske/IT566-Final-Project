
-- 03_views.sql (MySQL)
CREATE OR REPLACE VIEW v_campaign_channel_counts AS
SELECT
  c.campaign_id,
  c.name AS campaign_name,
  c.status,
  c.budget_cents,
  COUNT(x.channel_id) AS channel_count
FROM campaign c
LEFT JOIN campaign_channel_xref x ON x.campaign_id = c.campaign_id
GROUP BY c.campaign_id, c.name, c.status, c.budget_cents;

CREATE OR REPLACE VIEW v_channel_campaign_counts AS
SELECT
  ch.channel_id,
  ch.name AS channel_name,
  ch.type,
  COUNT(x.campaign_id) AS campaign_count
FROM channel ch
LEFT JOIN campaign_channel_xref x ON x.channel_id = ch.channel_id
GROUP BY ch.channel_id, ch.name, ch.type;
