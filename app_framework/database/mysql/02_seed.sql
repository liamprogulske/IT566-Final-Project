
-- 02_seed.sql (MySQL)
INSERT IGNORE INTO channel(name, type) VALUES
  ('Google Ads', 'search'),
  ('Meta Ads', 'social'),
  ('Programmatic Display', 'display'),
  ('Email Platform', 'email');

INSERT INTO campaign(name, start_date, end_date, status, budget_cents) VALUES
  ('Holiday 2025 Awareness', '2025-11-01', '2025-12-31', 'active', 2500000),
  ('Q4 Retargeting', '2025-10-01', '2025-12-31', 'paused', 1500000),
  ('Email Reactivation', '2025-09-15', '2025-11-30', 'draft', 500000);

INSERT IGNORE INTO campaign_channel_xref(campaign_id, channel_id)
SELECT c.campaign_id, ch.channel_id
FROM campaign c
JOIN channel ch
  ON (c.name='Holiday 2025 Awareness' AND ch.name IN ('Google Ads','Meta Ads'))
  OR (c.name='Q4 Retargeting' AND ch.name='Programmatic Display')
  OR (c.name='Email Reactivation' AND ch.name='Email Platform');
