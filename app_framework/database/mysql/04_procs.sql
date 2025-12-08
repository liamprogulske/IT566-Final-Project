DELIMITER $$

DROP PROCEDURE IF EXISTS sp_get_campaigns_for_channel$$
CREATE PROCEDURE sp_get_campaigns_for_channel(IN p_channel_id INT)
BEGIN
  SELECT c.*
  FROM campaign c
  JOIN campaign_channel_xref x ON x.campaign_id = c.campaign_id
  WHERE x.channel_id = p_channel_id
  ORDER BY c.name;
END$$

DROP PROCEDURE IF EXISTS sp_get_channels_for_campaign$$
CREATE PROCEDURE sp_get_channels_for_campaign(IN p_campaign_id INT)
BEGIN
  SELECT ch.*
  FROM channel ch
  JOIN campaign_channel_xref x ON x.channel_id = ch.channel_id
  WHERE x.campaign_id = p_campaign_id
  ORDER BY ch.name;
END$$

DELIMITER ;