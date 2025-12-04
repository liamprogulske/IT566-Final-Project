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

    def create(self, name, start_date=None, end_date=None, budget_cents=0):
        sql = """INSERT INTO campaign(name,start_date,end_date,budget_cents)
                 VALUES(%s,%s,%s,%s)"""
        with DB.conn() as cn, cn.cursor() as cur:
            cur.execute(sql, (name, start_date, end_date, budget_cents))
            cn.commit()
            return cur.lastrowid

    def update(self, campaign_id, **fields):
        keys = list(fields.keys())
        if not keys: return 0
        sets = ", ".join(f"{k}=%s" for k in keys)
        sql = f"UPDATE campaign SET {sets} WHERE campaign_id=%s"
        vals = [fields[k] for k in keys] + [campaign_id]
        with DB.conn() as cn, cn.cursor() as cur:
            cur.execute(sql, vals); cn.commit()
            return cur.rowcount

    def delete(self, campaign_id):
        with DB.conn() as cn, cn.cursor() as cur:
            cur.execute("DELETE FROM campaign WHERE campaign_id=%s", (campaign_id,))
            cn.commit(); return cur.rowcount
