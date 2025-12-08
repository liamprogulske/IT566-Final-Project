from __future__ import annotations

from typing import Optional, List, Dict

from .db import DB, row_to_dict


class ChannelDAO:
    """
    Data Access Object for the 'channel' table.

    Schema (as used in UI):
      channel_id INT PK AUTO_INCREMENT
      name       VARCHAR(...)
      type       VARCHAR(...)   -- sometimes called 'platform' in UI text
      created_at TIMESTAMP
    """

    # -------------------------------------------------------------- #
    # READ
    # -------------------------------------------------------------- #
    def get(self, channel_id: int) -> Optional[Dict]:
        sql = "SELECT * FROM channel WHERE channel_id = %s"
        conn = DB.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql, (channel_id,))
            row = cur.fetchone()
            return row_to_dict(cur, row)
        finally:
            cur.close()
            conn.close()

    def list(
        self,
        limit: int = 100,
        offset: int = 0,
        q: Optional[str] = None,
    ) -> List[Dict]:
        base = "SELECT * FROM channel"
        params: list = []

        if q:
            base += " WHERE name LIKE %s"
            params.append(f"%{q}%")

        base += " ORDER BY channel_id LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        conn = DB.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(base, tuple(params))
            rows = cur.fetchall()
            return [row_to_dict(cur, r) for r in rows]
        finally:
            cur.close()
            conn.close()

    # -------------------------------------------------------------- #
    # CREATE
    # -------------------------------------------------------------- #
    def create(self, name: str, ch_type: str = "Other") -> int:
        """
        Create a channel.

        Only 'name' and 'type' are stored because the schema defines:
          channel_id, name, type, created_at
        """
        sql = """
            INSERT INTO channel (name, type)
            VALUES (%s, %s)
        """
        conn = DB.get_connection()
        try:
            cur = conn.cursor()
            # IMPORTANT: parameters must be a tuple, not a bare string
            cur.execute(sql, (name, ch_type))
            conn.commit()
            return cur.lastrowid
        finally:
            cur.close()
            conn.close()

    # -------------------------------------------------------------- #
    # UPDATE
    # -------------------------------------------------------------- #
    def update(self, channel_id: int, **fields) -> int:
        """
        Update arbitrary fields on a channel.

        Example usage:
          update(1, name="Email (Updated)", type="Email")
        """
        keys = list(fields.keys())
        if not keys:
            return 0

        set_clause = ", ".join(f"{k} = %s" for k in keys)
        sql = f"UPDATE channel SET {set_clause} WHERE channel_id = %s"
        params = [fields[k] for k in keys] + [channel_id]

        conn = DB.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            conn.commit()
            return cur.rowcount
        finally:
            cur.close()
            conn.close()

    # -------------------------------------------------------------- #
    # DELETE
    # -------------------------------------------------------------- #
    def delete(self, channel_id: int) -> int:
        """
        Delete a channel by ID.
        Because of ON DELETE CASCADE on campaign_channel_xref (if configured),
        this will also remove its mappings.
        """
        sql = "DELETE FROM channel WHERE channel_id = %s"
        conn = DB.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql, (channel_id,))
            conn.commit()
            return cur.rowcount
        finally:
            cur.close()
            conn.close()
