USE it566_project_db;

DROP PROCEDURE IF EXISTS upsert_campaign_daily_metrics;

DELIMITER $$

CREATE PROCEDURE upsert_campaign_daily_metrics(
    IN p_campaign_id  INT,
    IN p_metric_date  DATE,
    IN p_impressions  INT,
    IN p_clicks       INT,
    IN p_cost_cents   INT
)
BEGIN
    INSERT INTO campaign_daily_metrics (
        campaign_id,
        metric_date,
        impressions,
        clicks,
        cost_cents
    )
    VALUES (
        p_campaign_id,
        p_metric_date,
        p_impressions,
        p_clicks,
        p_cost_cents
    )
    ON DUPLICATE KEY UPDATE
        impressions = p_impressions,
        clicks      = p_clicks,
        cost_cents  = p_cost_cents;
END$$

DELIMITER ;
