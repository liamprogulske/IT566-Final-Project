from .db import DB, row_to_dict

class CampaignDAO:
    def get(self, campaign_id):
        sql = "SELECT * FROM campaign WHERE campaign_id=%s"
        with DB.conn() as cn, cn.cursor() as cur:
            cur.execute(sql, (campaign_id,))
            r = cur.fetchone()
            return row_to_dict(cur, r) if r else None

    def list(self, limit=50, offset=0, q=None):
        base = "SELECT * FROM campaign"
        args = []
        if q:
            base += " WHERE name LIKE %s"
            args.append(f"%{q}%")
        base += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        args += [limit, offset]
        with DB.conn() as cn, cn.cursor() as cur:
            cur.execute(base, tuple(args))
            return [row_to_dict(cur, r) for r in cur.fetchall()]

#----------------------------------------------------------#
#------------------------CREATE----------------------------#
#----------------------------------------------------------#

    def create(self, name, start_date=None, end_date=None, budget_cents=0, description=None):
        """
        Create a campaign.

        'description' is accepted for compatibility with the service layer,
        but is currently not stored in the database because the schema
        does not define a description column.
        """
        conn = DB.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO campaign (name, start_date, end_date, budget_cents)
                VALUES (%s, %s, %s, %s)
                """,
                (name, start_date, end_date, budget_cents),
            )
            conn.commit()
            return cur.lastrowid
        finally:
            cur.close()
            conn.close()

#----------------------------------------------------------#
#------------------------UPDATE----------------------------#
#----------------------------------------------------------#


    def update(self, campaign_id, **fields):
        keys = list(fields.keys())
        if not keys: return 0
        sets = ", ".join(f"{k}=%s" for k in keys)
        sql = f"UPDATE campaign SET {sets} WHERE campaign_id=%s"
        vals = [fields[k] for k in keys] + [campaign_id]
        with DB.conn() as cn, cn.cursor() as cur:
            cur.execute(sql, vals); cn.commit()
            return cur.rowcount

#----------------------------------------------------------#
#------------------------DELETE----------------------------#
#----------------------------------------------------------#

    def delete(self, campaign_id: int) -> int:
        """
        Delete a campaign by ID.
        Because of ON DELETE CASCADE on campaign_channel_xref,
        this will also remove its mappings.
        Returns the number of rows deleted (0 or 1).
        """
        conn = DB.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM campaign WHERE campaign_id = %s", (campaign_id,))
            conn.commit()
            return cur.rowcount
        finally:
            cur.close()
            conn.close()
        

def set_status(self, campaign_id: int, status: str) -> bool:
    """
    Update the status of a campaign.
    Returns True if updated, False if no campaign was found.
    """
    conn = DB.get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE campaign SET status = %s WHERE campaign_id = %s",
            (status, campaign_id),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        cur.close()
        conn.close()