"""
Database Connection Pool Manager using asynccontextmanager
"""
import os
import asyncio
from contextlib import asynccontextmanager
from psycopg_pool import AsyncConnectionPool
from src.utils.logger import logger
from dotenv import load_dotenv

load_dotenv()

class DatabasePoolManager:
    def __init__(self):
        self.pool = None
        self.db_uri = os.getenv("DB_URI")
        
    async def create_pool(self):
        """Create and open connection pool"""
        if self.pool is None:
            logger.info("Creating database connection pool...")
            self.pool = AsyncConnectionPool(
                self.db_uri,
                kwargs={
                    "autocommit": True,
                    "prepare_threshold": None,
                },
                min_size=15,     # Balanced for production
                max_size=200,     # Handle traffic spikes
                timeout=30,      # Prevent infinite waits
                open=False
            )
            await self.pool.open()
            logger.info(f"Database pool opened successfully with {15} min connections and {200} max connections")
        
    async def get_pool(self):
        """Get the connection pool"""
        if self.pool is None:
            await self.create_pool()
        return self.pool
        
    async def close_pool(self):
        """Close connection pool gracefully"""
        if self.pool:
            logger.info("Closing database connection pool...")
            await self.pool.close()
            logger.info("Database pool closed successfully")
            self.pool = None

# Global pool manager instance
pool_manager = DatabasePoolManager()

@asynccontextmanager
async def database_lifespan():
    """Context manager for database lifecycle"""
    # Startup
    await pool_manager.create_pool()
    try:
        yield pool_manager
    finally:
        # Shutdown
        await pool_manager.close_pool()

async def get_connection_pool():
    """Get connection pool for use in routers"""
    return await pool_manager.get_pool()
