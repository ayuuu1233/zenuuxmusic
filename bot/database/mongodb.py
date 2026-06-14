"""
MongoDB connection manager using Motor for async operations.
Handles database initialization and connection pooling.
"""

from typing import Optional
from motor.motor_asyncio import (
    AsyncClient,
    AsyncDatabase,
    AsyncCollection,
)
import config
from bot.logger import db_logger


class MongoDB:
    """Async MongoDB connection manager."""

    def __init__(self) -> None:
        """Initialize MongoDB connection manager."""
        self._client: Optional[AsyncClient] = None
        self._database: Optional[AsyncDatabase] = None

    async def connect(self) -> None:
        """
        Establish connection to MongoDB.
        
        Raises:
            ConnectionError: If connection fails
        """
        try:
            self._client = AsyncClient(config.MONGODB_URI)
            # Test connection
            await self._client.admin.command("ping")
            self._database = self._client[config.MONGODB_DB_NAME]
            db_logger.info(f"Connected to MongoDB: {config.MONGODB_DB_NAME}")
        except Exception as e:
            db_logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self._client:
            self._client.close()
            db_logger.info("Disconnected from MongoDB")

    @property
    def database(self) -> AsyncDatabase:
        """Get MongoDB database instance."""
        if self._database is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._database

    def collection(self, name: str) -> AsyncCollection:
        """
        Get a specific collection.
        
        Args:
            name: Collection name
            
        Returns:
            AsyncCollection: MongoDB collection instance
        """
        return self.database[name]


# Global database instance
db = MongoDB()
