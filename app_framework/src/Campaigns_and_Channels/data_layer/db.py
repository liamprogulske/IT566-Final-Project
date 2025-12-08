# app_framework/src/Campaigns_and_Channels/data_layer/db.py

import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool
from mysql.connector import Error


class DB:
    _pool: MySQLConnectionPool | None = None

    @classmethod
    def init_pool(cls, cfg: dict) -> None:
        """
        Initialize the connection pool once from JSON config dict.

        Expected shape:
        cfg["database"]["pool"]["name"]
        cfg["database"]["pool"]["size"]
        cfg["database"]["connection"]["config"]  -> dict(host, port, user, password, database)
        """
        if cls._pool is not None:
            return

        cls._pool = MySQLConnectionPool(
            pool_name=cfg["database"]["pool"]["name"],
            pool_size=cfg["database"]["pool"]["size"],
            **cfg["database"]["connection"]["config"],
        )

    @classmethod
    def get_connection(cls) -> mysql.connector.connection.MySQLConnection:
        """Get a pooled MySQL connection. Call .close() when done."""
        if cls._pool is None:
            raise RuntimeError("DB pool not initialized")
        return cls._pool.get_connection()


def row_to_dict(cursor, row):
    """Convert a row + cursor.description to a dict."""
    if row is None:
        return None
    return {desc[0]: value for desc, value in zip(cursor.description, row)}

""" def upsert_campaign_daily_metrics(campaign_id, metric_date, impressions, clicks, cost_cents):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.callproc(
            "upsert_campaign_daily_metrics",
            [campaign_id, metric_date, impressions, clicks, cost_cents],
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def get_campaign_performance(campaign_id=None):
    
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        sql = "SELECT * FROM v_campaign_performance"
        params = []
        if campaign_id is not None:
            sql += " WHERE campaign_id = %s"
            params.append(campaign_id)
        sql += " ORDER BY campaign_id"
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
 """