
-- 99_teardown.sql (MySQL)
SET FOREIGN_KEY_CHECKS=0;
DROP VIEW IF EXISTS v_channel_campaign_counts;
DROP VIEW IF EXISTS v_campaign_channel_counts;
DROP PROCEDURE IF EXISTS sp_get_campaigns_for_channel;
DROP PROCEDURE IF EXISTS sp_get_channels_for_campaign;
DROP TABLE IF EXISTS campaign_channel_xref;
DROP TABLE IF EXISTS campaign;
DROP TABLE IF EXISTS channel;
SET FOREIGN_KEY_CHECKS=1;
