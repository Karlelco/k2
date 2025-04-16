import os
from psycopg2 import pool
from dotenv import load_dotenv

# Load .env file (make sure DATABASE_URL is set)
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

def store_in_database(data):
    """Store the scraped data in the Neon PostgreSQL database"""
    logger.info("Storing data in Neon PostgreSQL database...")

    connection_pool = None
    conn = None
    cur = None
    try:
        # Create a connection pool (minconn, maxconn, dsn)
        connection_pool = pool.SimpleConnectionPool(
            1,  # Minimum number of connections in the pool
            10,  # Maximum number of connections in the pool
            DATABASE_URL
        )

        if connection_pool:
            logger.info("Connection pool created successfully")

        # Get a connection from the pool
        conn = connection_pool.getconn()
        cur = conn.cursor()

        # ... (your database logic here, as in your original code)
        # Example: cur.execute("SQL", (...))

        conn.commit()
        logger.info("Database transaction committed successfully")

    except Exception as e:
        logger.error(f"Error storing data in database: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
        if connection_pool:
            connection_pool.closeall()