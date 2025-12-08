-- IT566 PROJECT DB INSPECTION (With Vertical Column Separators)

USE it566_project_db;


-- ==================================================
-- CHANNELS (WITH PIPES)
-- ==================================================
SELECT '--------------- CHANNELS ---------------' AS '';

-- Header row
SELECT
  CONCAT(
    LPAD('ID', 4, ' '), ' | ',
    RPAD('NAME', 25, ' '), ' | ',
    RPAD('TYPE', 10, ' '), ' | ',
    'CREATED_AT'
  ) AS '';

-- Data rows
SELECT
  CONCAT(
    LPAD(channel_id, 4, ' '), ' | ',
    RPAD(name, 25, ' '), ' | ',
    RPAD(type, 10, ' '), ' | ',
    created_at
  ) AS ''
FROM channel
ORDER BY channel_id;


-- ==================================================
-- 📌 CAMPAIGNS (WITH PIPES)
-- ==================================================
SELECT '--------------- CAMPAIGNS ---------------' AS '';

SELECT
  CONCAT(
    LPAD('ID', 4, ' '), ' | ',
    RPAD('NAME', 25, ' '), ' | ',
    RPAD('STATUS', 10, ' '), ' | ',
    LPAD('BUDGET_CENTS', 12, ' '), ' | ',
    LPAD('BUDGET_USD', 12, ' '), ' | ',
    'CREATED_AT'
  ) AS '';

SELECT
  CONCAT(
    LPAD(campaign_id, 4, ' '), ' | ',
    RPAD(name, 25, ' '), ' | ',
    RPAD(status, 10, ' '), ' | ',
    LPAD(budget_cents, 12, ' '), ' | ',
    LPAD(ROUND(budget_cents/100,2), 12, ' '), ' | ',
    created_at
  ) AS ''
FROM campaign
ORDER BY campaign_id;


-- ==================================================
-- CAMPAIGN ↔ CHANNEL MAPPINGS
-- ==================================================
SELECT '---- CAMPAIGN TO CHANNEL MAPPINGS ----' AS '';

SELECT
  CONCAT(
    LPAD('CMP_ID', 6, ' '), ' | ',
    RPAD('CAMPAIGN', 25, ' '), ' | ',
    LPAD('CH_ID', 6, ' '), ' | ',
    RPAD('CHANNEL', 25, ' ')
  ) AS '';

SELECT
  CONCAT(
    LPAD(ccx.campaign_id, 6, ' '), ' | ',
    RPAD(c.name, 25, ' '), ' | ',
    LPAD(ccx.channel_id, 6, ' '), ' | ',
    RPAD(ch.name, 25, ' ')
  ) AS ''
FROM campaign_channel_xref ccx
JOIN campaign c ON ccx.campaign_id = c.campaign_id
JOIN channel ch ON ccx.channel_id = ch.channel_id
ORDER BY ccx.campaign_id, ccx.channel_id;


SELECT '---------------- END OF REPORT ----------------' AS '';
