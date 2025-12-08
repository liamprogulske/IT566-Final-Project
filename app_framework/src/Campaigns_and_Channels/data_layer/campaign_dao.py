from .db import DB, row_to_dict

class CampaignDAO:
    def get(self, campaign_id: int):
        sql = "SELECT * FROM campaign WHERE campaign_id=%s"
        conn = DB.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql, (campaign_id,))
            row = cur.fetchone()
            return row_to_dict(cur, row)
        finally:
            cur.close()
            conn.close()

    def list(self, limit=50, offset=0, q=None):
        base = "SELECT * FROM campaign"
        args = []
        if q:
            base += " WHERE name LIKE %s"
            args.append(f"%{q}%")
        base += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        args += [limit, offset]

        conn = DB.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(base, tuple(args))
            rows = cur.fetchall()
            return [row_to_dict(cur, r) for r in rows]
        finally:
            cur.close()
            conn.close()

    def create(self, name, start_date=None, end_date=None, budget_cents=0):
        sql = """
            INSERT INTO campaign (name, start_date, end_date, budget_cents)
            VALUES (%s, %s, %s, %s)
        """
        conn = DB.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql, (name, start_date, end_date, budget_cents))
            conn.commit()
            return cur.lastrowid
        finally:
            cur.close()
            conn.close()

    def update(self, campaign_id, **fields):
        keys = list(fields.keys())
        if not keys:
            return 0
        set_clause = ", ".join(f"{k} = %s" for k in keys)
        sql = f"UPDATE campaign SET {set_clause} WHERE campaign_id = %s"
        params = [fields[k] for k in keys] + [campaign_id]

        conn = DB.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            conn.commit()
            return cur.rowcount
        finally:
            cur.close()
            conn.close()

    def delete(self, campaign_id: int) -> int:
        sql = "DELETE FROM campaign WHERE campaign_id = %s"
        conn = DB.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql, (campaign_id,))
            conn.commit()
            return cur.rowcount
        finally:
            cur.close()
            conn.close()

    def set_status(self, campaign_id: int, status: str) -> bool:
        sql = "UPDATE campaign SET status = %s WHERE campaign_id = %s"
        conn = DB.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql, (status, campaign_id))
            conn.commit()
            return cur.rowcount > 0
        finally:
            cur.close()
            conn.close()
