# Campaigns_And_Channels/data_layer/campaign_channel_xref_dao.py
from typing import List, Dict, Optional, Tuple
from mysql.connector import errors as mysql_errors

from .db import DB, row_to_dict


class CampaignChannelXrefDAO:
    """
    Data access for the campaign_channel_xref table.

    Expected schema (typical):
      campaign_channel_xref(
          campaign_id INT NOT NULL,
          channel_id  INT NOT NULL,
          PRIMARY KEY (campaign_id, channel_id),
          FOREIGN KEY (campaign_id) REFERENCES campaign(campaign_id) ON DELETE CASCADE,
          FOREIGN KEY (channel_id)  REFERENCES channel(channel_id)  ON DELETE CASCADE
      )
    """

    # -------------------------
    # Write operations
    # -------------------------
    def link(self, campaign_id: int, channel_id: int) -> bool:
        """
        Link a campaign to a channel.
        Returns True if inserted, False if it already existed.
        """
        sql = """
            INSERT IGNORE INTO campaign_channel_xref (campaign_id, channel_id)
            VALUES (%s, %s)
        """
        with DB.conn() as cn, cn.cursor() as cur:
            cur.execute(sql, (campaign_id, channel_id))
            cn.commit()
            return cur.rowcount == 1  # 1 = inserted; 0 = already existed

    def unlink(self, campaign_id: int, channel_id: int) -> int:
        """
        Unlink a campaign from a channel.
        Returns the number of rows deleted (0 or 1).
        """
        sql = """
            DELETE FROM campaign_channel_xref
            WHERE campaign_id = %s AND channel_id = %s
        """
        with DB.conn() as cn, cn.cursor() as cur:
            cur.execute(sql, (campaign_id, channel_id))
            cn.commit()
            return cur.rowcount

    def purge_campaign(self, campaign_id: int) -> int:
        """Delete all links for a given campaign. Returns rows deleted."""
        sql = "DELETE FROM campaign_channel_xref WHERE campaign_id = %s"
        with DB.conn() as cn, cn.cursor() as cur:
            cur.execute(sql, (campaign_id,))
            cn.commit()
            return cur.rowcount

    def purge_channel(self, channel_id: int) -> int:
        """Delete all links for a given channel. Returns rows deleted."""
        sql = "DELETE FROM campaign_channel_xref WHERE channel_id = %s"
        with DB.conn() as cn, cn.cursor() as cur:
            cur.execute(sql, (channel_id,))
            cn.commit()
            return cur.rowcount

    # -------------------------
    # Read operations
    # -------------------------
    def exists(self, campaign_id: int, channel_id: int) -> bool:
        """Return True if a link exists."""
        sql = """
            SELECT 1 FROM campaign_channel_xref
            WHERE campaign_id = %s AND channel_id = %s
            LIMIT 1
        """
        with DB.conn() as cn, cn.cursor() as cur:
            cur.execute(sql, (campaign_id, channel_id))
            return cur.fetchone() is not None

    def list_channels_for_campaign(self, campaign_id: int) -> List[Dict]:
        """
        Return channel rows linked to a campaign.
        """
        sql = """
            SELECT ch.*
            FROM campaign_channel_xref x
            JOIN channel ch ON ch.channel_id = x.channel_id
            WHERE x.campaign_id = %s
            ORDER BY ch.name
        """
        with DB.conn() as cn, cn.cursor() as cur:
            cur.execute(sql, (campaign_id,))
            return [row_to_dict(cur, r) for r in cur.fetchall()]

    def list_campaigns_for_channel(self, channel_id: int) -> List[Dict]:
        """
        Return campaign rows linked to a channel.
        """
        sql = """
            SELECT c.*
            FROM campaign_channel_xref x
            JOIN campaign c ON c.campaign_id = x.campaign_id
            WHERE x.channel_id = %s
            ORDER BY c.created_at DESC, c.campaign_id DESC
        """
        with DB.conn() as cn, cn.cursor() as cur:
            cur.execute(sql, (channel_id,))
            return [row_to_dict(cur, r) for r in cur.fetchall()]

    def list_links(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        List raw pairs (campaign_id, channel_id). Useful for debugging.
        """
        sql = """
            SELECT campaign_id, channel_id
            FROM campaign_channel_xref
            ORDER BY campaign_id, channel_id
            LIMIT %s OFFSET %s
        """
        with DB.conn() as cn, cn.cursor() as cur:
            cur.execute(sql, (limit, offset))
            return [row_to_dict(cur, r) for r in cur.fetchall()]

    def counts(self) -> Dict[str, int]:
        """
        Return counts for dashboard-ish display.
        {
          "links": <total links>,
          "campaigns_with_channels": <distinct campaigns linked>,
          "channels_with_campaigns": <distinct channels linked>
        }
        """
        sql_total = "SELECT COUNT(*) FROM campaign_channel_xref"
        sql_c = "SELECT COUNT(DISTINCT campaign_id) FROM campaign_channel_xref"
        sql_h = "SELECT COUNT(DISTINCT channel_id)  FROM campaign_channel_xref"
        with DB.conn() as cn, cn.cursor() as cur:
            cur.execute(sql_total); links = cur.fetchone()[0]
            cur.execute(sql_c); campaigns_distinct = cur.fetchone()[0]
            cur.execute(sql_h); channels_distinct = cur.fetchone()[0]
        return {
            "links": links,
            "campaigns_with_channels": campaigns_distinct,
            "channels_with_campaigns": channels_distinct,
        }
