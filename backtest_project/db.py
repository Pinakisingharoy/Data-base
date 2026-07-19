from contextlib import contextmanager
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import config

connection_pool = None

def initialize_connection_pool():
    global connection_pool
    if connection_pool is None:
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            host=config.DB_HOST,
            port=config.DB_PORT,
            database=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD
        )
        print("✅ PostgreSQL connection pool created.")

def get_connection():
    global connection_pool
    if connection_pool is None:
        initialize_connection_pool()
    return connection_pool.getconn()

def release_connection(conn):
    global connection_pool
    if conn and connection_pool:
        connection_pool.putconn(conn)

def close_pool():
    global connection_pool
    if connection_pool:
        connection_pool.closeall()
        print("Database pool closed.")

@contextmanager
def get_cursor():
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        yield conn, cursor
        conn.commit()
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            release_connection(conn)

def fetch_all(query, params=None):
    with get_cursor() as (_, cursor):
        cursor.execute(query, params)
        return cursor.fetchall()

def fetch_one(query, params=None):
    with get_cursor() as (_, cursor):
        cursor.execute(query, params)
        return cursor.fetchone()