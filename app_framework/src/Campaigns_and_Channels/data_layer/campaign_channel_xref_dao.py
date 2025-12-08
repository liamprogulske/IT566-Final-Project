from __future__ import annotations

from datetime import date
from typing import List, Dict, Optional

from .db import DB, row_to_dict


class CampaignChannelXrefDAO:
    """
    Data Access Object that manages:
      - The many-to-many mapping table: campaign_channel_xref
      - Optional campaign_daily_metrics table for performance aggregation.
    """
    # ---------------------------------------------------------- #
    # LINK / UNLINK
    # ---------------------------------------------------------- #
    def link(self, campaign_id: int, channel_id: int) -> bool:
        """
        Insert a mapping if it does not exist.
        Returns True if newly added, False if already existed.
        """
        sql_check = """
            SELECT 1 FROM campaign_channel_xref
            WHERE campaign_id = %s AND channel_id = %s
        """
        sql_insert = """
            INSERT INTO campaign_channel_xref (campaign_id, channel_id)
            VALUES (%s, %s)
        """

        conn = DB.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql_check, (campaign_id, channel_id))
            if cur.fetchone():
                return False  # already linked

            cur.execute(sql_insert, (campaign_id, channel_id))
            conn.commit()
            return True
        finally:
            cur.close()
            conn.close()

    def unlink(self, campaign_id: int, channel_id: int) -> int:
        """
        Remove a single campaign ↔ channel mapping.
        Returns number of rows deleted (0 or 1).
        """
        sql = """
            DELETE FROM campaign_channel_xref
            WHERE campaign_id = %s AND channel_id = %s
        """
        conn = DB.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql, (campaign_id, channel_id))
            conn.commit()
            return cur.rowcount
        finally:
            cur.close()
            conn.close()

    # ---------------------------------------------------------- #
    # LIST: Channels for Campaign
    # ---------------------------------------------------------- #
    def list_channels_for_campaign(self, campaign_id: int) -> List[Dict]:
        """
        Return a list of channel rows linked to a campaign.
        """
        sql = """
            SELECT ch.*
            FROM channel ch
            JOIN campaign_channel_xref ccx
              ON ccx.channel_id = ch.channel_id
            WHERE ccx.campaign_id = %s
            ORDER BY ch.channel_id
        """
        conn = DB.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql, (campaign_id,))
            rows = cur.fetchall()
            return [row_to_dict(cur, r) for r in rows]
        finally:
            cur.close()
            conn.close()

    # ---------------------------------------------------------- #
    # UPSERT DAILY METRICS
    # ---------------------------------------------------------- #
    def upsert_campaign_daily_metrics(
        self,
        campaign_id: int,
        metric_date: date,
        impressions: int = 0,
        clicks: int = 0,
        spend_cents: int = 0,
        revenue_cents: int = 0,
    ) -> None:
        """
        Insert or update a row in campaign_daily_metrics.

        Uses composite PK (campaign_id, metric_date) and
        ON DUPLICATE KEY UPDATE to perform the upsert.
        """
        sql = """
            INSERT INTO campaign_daily_metrics (
                campaign_id, metric_date, impressions, clicks, spend_cents, revenue_cents
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
              impressions = VALUES(impressions),
              clicks      = VALUES(clicks),
              spend_cents = VALUES(spend_cents),
              revenue_cents = VALUES(revenue_cents)
        """
        conn = DB.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                sql,
                (campaign_id, metric_date, impressions, clicks, spend_cents, revenue_cents),
            )
            conn.commit()
        finally:
            cur.close()
            conn.close()

    # ---------------------------------------------------------- #
    # CAMPAIGN PERFORMANCE (AGGREGATED)
    # ---------------------------------------------------------- #
    def get_campaign_performance(
        self,
        campaign_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict:
        """
        Aggregate performance metrics for a campaign over an optional date range.

        Returns a dict with:
          - impressions, clicks, spend_cents, revenue_cents
          - ctr (click-through rate)
          - cpc (cost per click)
          - roas (revenue / spend, if revenue is provided)
        """
        base_sql = """
            SELECT
                COALESCE(SUM(impressions), 0)   AS impressions,
                COALESCE(SUM(clicks), 0)        AS clicks,
                COALESCE(SUM(spend_cents), 0)   AS spend_cents,
                COALESCE(SUM(revenue_cents), 0) AS revenue_cents
            FROM campaign_daily_metrics
            WHERE campaign_id = %s
        """

        params: list = [campaign_id]

        if start_date is not None:
            base_sql += " AND metric_date >= %s"
            params.append(start_date)
        if end_date is not None:
            base_sql += " AND metric_date <= %s"
            params.append(end_date)

        conn = DB.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(base_sql, tuple(params))
            row = cur.fetchone()
        finally:
            cur.close()
            conn.close()

        if row is None:
            impressions = clicks = spend_cents = revenue_cents = 0
        else:
            # Convert Decimal/MySQL values to python ints
            impressions = int(row[0] or 0)
            clicks = int(row[1] or 0)
            spend_cents = int(row[2] or 0)
            revenue_cents = int(row[3] or 0)

        # Safe computed metrics
        ctr = (clicks / impressions) if impressions > 0 else 0.0
        cpc = (spend_cents / clicks) / 100.0 if clicks > 0 else 0.0  # USD/click
        roas = (revenue_cents / spend_cents) if spend_cents > 0 else 0.0

        return {
            "campaign_id": campaign_id,
            "impressions": impressions,
            "clicks": clicks,
            "spend_cents": spend_cents,
            "revenue_cents": revenue_cents,
            "ctr": ctr,
            "cpc": cpc,
            "roas": roas,
            "start_date": start_date,
            "end_date": end_date,
        }

    # ---------------------------------------------------------- #
    # COUNTS & REPORTING HELPERS
    # ---------------------------------------------------------- #
    def count_campaigns_for_channel(self, channel_id: int) -> int:
        """
        Return how many campaigns are linked to a given channel.
        Used for safe delete logic in the service layer.
        """
        sql = """
            SELECT COUNT(*)
            FROM campaign_channel_xref
            WHERE channel_id = %s
        """
        conn = DB.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql, (channel_id,))
            (count,) = cur.fetchone()
            return int(count or 0)
        finally:
            cur.close()
            conn.close()

    def list_all_mappings(self) -> List[Dict]:
        """
        Return all campaign ↔ channel mappings with names, for reporting.
        """
        sql = """
            SELECT
                ccx.campaign_id,
                c.name AS campaign_name,
                ccx.channel_id,
                ch.name AS channel_name
            FROM campaign_channel_xref ccx
            JOIN campaign c ON ccx.campaign_id = c.campaign_id
            JOIN channel ch ON ccx.channel_id = ch.channel_id
            ORDER BY ccx.campaign_id, ccx.channel_id
        """
        conn = DB.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
            return [row_to_dict(cur, r) for r in rows]
        finally:
            cur.close()
            conn.close()
