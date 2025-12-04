# /data_layer/channel_dao.py
from typing import List, Dict, Optional
from mysql.connector import errors as mysql_errors
from .db import DB, row_to_dict


class ChannelDAO:
    """
    Data Access Object for the `channel` table.

    Expected table schema (from your SQL setup):
      channel (
          channel_id INT AUTO_INCREMENT PRIMARY KEY,
          name VARCHAR(100) NOT NULL,
          description TEXT NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    """

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------
    def create(self, name: str, description: Optional[str] = None) -> int:
        """
        Insert a new channel record and return its ID.
        """
        sql = """
            INSERT INTO channel (name, description)
            VALUES (%s, %s)
        """
        with DB.conn() as cn, cn.cursor() as cur:
            try:
                cur.execute(sql, (name, description))
                cn.commit()
                return cur.lastrowid
            except mysql_errors.IntegrityError as e:
                raise ValueError(f"Channel with name '{name}' already exists.") from e

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------
    def get(self, channel_id: int) -> Optional[Dict]:
        """
        Fetch one channel by ID.
        """
        sql = "SELECT * FROM channel WHERE channel_id = %s"
        with DB.conn() as cn, cn.cursor() as cur:
            cur.execute(sql, (channel_id,))
            row = cur.fetchone()
            return row_to_dict(cur, row) if row else None

    def list(self, limit: int = 100, offset: int = 0, q: Optional[str] = None) -> List[Dict]:
        """
        Return all channels (optionally filtered by search term).
        """
        sql = "SELECT * FROM channel"
        args = []
        if q:
            sql += " WHERE name LIKE %s"
            args.append(f"%{q}%")
        sql += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        args += [limit, offset]

        with DB.conn() as cn, cn.cursor() as cur:
            cur.execute(sql, tuple(args))
            return [row_to_dict(cur, r) for r in cur.fetchall()]

    def get_by_name(self, name: str) -> Optional[Dict]:
        """
        Get a channel by its name.
        """
        sql = "SELECT * FROM channel WHERE name = %s LIMIT 1"
        with DB.conn() as cn, cn.cursor() as cur:
            cur.execute(sql, (name,))
            row = cur.fetchone()
            return row_to_dict(cur, row) if row else None

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------
    def update(self, channel_id: int, **fields) -> int:
        """
        Update one or more fields on a channel. Returns the number of affected rows.
        """
        if not fields:
            return 0
        cols = ", ".join(f"{k} = %s" for k in fields)
        sql = f"UPDATE channel SET {cols} WHERE channel_id = %s"
        vals = list(fields.values()) + [channel_id]

        with DB.conn() as cn, cn.cursor() as cur:
            cur.execute(sql, vals)
            cn.commit()
            return cur.rowcount

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------
    def delete(self, channel_id: int) -> int:
        """
        Delete a channel by ID. Returns number of rows deleted.
        """
        sql = "DELETE FROM channel WHERE channel_id = %s"
        with DB.conn() as cn, cn.cursor() as cur:
            cur.execute(sql, (channel_id,))
            cn.commit()
            return cur.rowcount
