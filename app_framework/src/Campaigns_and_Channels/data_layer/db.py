import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool
from mysql.connector import Error

class DB:
    _pool = None

    @classmethod
    def init_pool(cls, cfg):

        if cls._pool: return
        cls._pool = MySQLConnectionPool(
            pool_name=cfg['database']['pool']['name'],
            pool_size=cfg['database']['pool']['size'],
            **cfg['database']['connection']['config']
        )

    @classmethod
    def conn(cls):
        if not cls._pool:
            raise RuntimeError("DB pool not initialized")
        return cls._pool.get_connection()

    def row_to_dict(cursor, row):
        return {desc[0]: value for desc, value in zip(cursor.description, row)}
        if cls._pool is None:
            cls._pool = MySQLConnectionPool(
                pool_name=cfg["database"]["pool"]["name"],
                pool_size=cfg["database"]["pool"]["size"],
                **cfg["database"]["connection"]["config"],
            )

    @classmethod
    def get_connection(cls):
        """
        Get a pooled MySQL connection.
        Always close() it when done so it returns to the pool.
        """
        if cls._pool is None:
            raise RuntimeError("DB pool is not initialized. Call DB.init_pool(config) first.")
        return cls._pool.get_connection()

def row_to_dict(cursor, row):
    return {desc[0]: value for desc, value in zip(cursor.description, row)}

def get_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="root",
        database="it566_project_db",
    )


def upsert_campaign_daily_metrics(campaign_id, metric_date, impressions, clicks, cost_cents):
    """
    Upsert daily metrics for a campaign.

    metric_date: 'YYYY-MM-DD' string or date object
    """
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
    """
    Returns aggregated performance for all campaigns or a single one.
    """
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
