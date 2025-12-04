import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool

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