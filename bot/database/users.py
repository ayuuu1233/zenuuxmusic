"""
User database operations.
Manages user profiles, preferences, and statistics.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pymongo import ASCENDING

from bot.database.mongodb import db
from bot.logger import db_logger


class UserDB:
    """Handle user database operations."""

    COLLECTION_NAME = "users"

    @classmethod
    async def init_indexes(cls) -> None:
        """Initialize database indexes for users collection."""
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            await collection.create_index("user_id", unique=True)
            await collection.create_index("username")
            await collection.create_index("created_at")
            db_logger.info("User indexes initialized")
        except Exception as e:
            db_logger.error(f"Failed to initialize user indexes: {e}")

    @classmethod
    async def get_or_create_user(
        cls,
        user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get or create a user document.
        
        Args:
            user_id: Telegram user ID
            username: Username (optional)
            first_name: First name (optional)
            
        Returns:
            Dict: User document
        """
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            
            user = await collection.find_one({"user_id": user_id})
            
            if not user:
                user_doc = {
                    "user_id": user_id,
                    "username": username,
                    "first_name": first_name,
                    "created_at": datetime.utcnow(),
                    "last_seen": datetime.utcnow(),
                    "is_blacklisted": False,
                    "is_premium": False,
                    "premium_expires_at": None,
                    "language": "en",
                    "notifications_enabled": True,
                    "statistics": {
                        "total_plays": 0,
                        "total_skip": 0,
                        "total_duration_played": 0,
                    },
                }
                await collection.insert_one(user_doc)
                db_logger.info(f"User {user_id} created")
                return user_doc
            else:
                # Update last_seen
                await collection.update_one(
                    {"user_id": user_id},
                    {"$set": {"last_seen": datetime.utcnow()}},
                )
                return user
        except Exception as e:
            db_logger.error(f"Error in get_or_create_user: {e}")
            raise

    @classmethod
    async def get_user(cls, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user document by ID.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Dict or None: User document
        """
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            return await collection.find_one({"user_id": user_id})
        except Exception as e:
            db_logger.error(f"Error in get_user: {e}")
            return None

    @classmethod
    async def update_user(
        cls,
        user_id: int,
        update_data: Dict[str, Any],
    ) -> bool:
        """
        Update user document.
        
        Args:
            user_id: Telegram user ID
            update_data: Data to update
            
        Returns:
            bool: True if successful
        """
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            result = await collection.update_one(
                {"user_id": user_id},
                {"$set": update_data},
            )
            return result.modified_count > 0
        except Exception as e:
            db_logger.error(f"Error in update_user: {e}")
            return False

    @classmethod
    async def increment_stat(
        cls,
        user_id: int,
        stat_key: str,
        value: int = 1,
    ) -> bool:
        """
        Increment a user statistic.
        
        Args:
            user_id: Telegram user ID
            stat_key: Statistic key (e.g., "statistics.total_plays")
            value: Value to increment by
            
        Returns:
            bool: True if successful
        """
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            result = await collection.update_one(
                {"user_id": user_id},
                {"$inc": {stat_key: value}},
            )
            return result.modified_count > 0
        except Exception as e:
            db_logger.error(f"Error in increment_stat: {e}")
            return False

    @classmethod
    async def is_blacklisted(cls, user_id: int) -> bool:
        """
        Check if user is blacklisted.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            bool: True if blacklisted
        """
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            user = await collection.find_one(
                {"user_id": user_id},
                {"is_blacklisted": 1},
            )
            return user.get("is_blacklisted", False) if user else False
        except Exception as e:
            db_logger.error(f"Error in is_blacklisted: {e}")
            return False

    @classmethod
    async def blacklist_user(cls, user_id: int, reason: str = "") -> bool:
        """
        Blacklist a user.
        
        Args:
            user_id: Telegram user ID
            reason: Reason for blacklisting
            
        Returns:
            bool: True if successful
        """
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            result = await collection.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "is_blacklisted": True,
                        "blacklist_reason": reason,
                        "blacklist_date": datetime.utcnow(),
                    }
                },
            )
            db_logger.info(f"User {user_id} blacklisted: {reason}")
            return result.modified_count > 0
        except Exception as e:
            db_logger.error(f"Error in blacklist_user: {e}")
            return False

    @classmethod
    async def unblacklist_user(cls, user_id: int) -> bool:
        """
        Unblacklist a user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            bool: True if successful
        """
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            result = await collection.update_one(
                {"user_id": user_id},
                {
                    "$set": {"is_blacklisted": False},
                    "$unset": {"blacklist_reason": "", "blacklist_date": ""},
                },
            )
            db_logger.info(f"User {user_id} unblacklisted")
            return result.modified_count > 0
        except Exception as e:
            db_logger.error(f"Error in unblacklist_user: {e}")
            return False

    @classmethod
    async def is_premium(cls, user_id: int) -> bool:
        """
        Check if user has active premium.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            bool: True if premium and not expired
        """
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            user = await collection.find_one(
                {"user_id": user_id},
                {"is_premium": 1, "premium_expires_at": 1},
            )
            
            if not user:
                return False
            
            if not user.get("is_premium", False):
                return False
            
            expires_at = user.get("premium_expires_at")
            if expires_at and expires_at < datetime.utcnow():
                # Expired, update status
                await cls.update_user(user_id, {"is_premium": False})
                return False
            
            return True
        except Exception as e:
            db_logger.error(f"Error in is_premium: {e}")
            return False

    @classmethod
    async def add_premium(
        cls,
        user_id: int,
        days: int = 30,
    ) -> bool:
        """
        Add premium to user.
        
        Args:
            user_id: Telegram user ID
            days: Number of days to add premium
            
        Returns:
            bool: True if successful
        """
        try:
            expires_at = datetime.utcnow() + timedelta(days=days)
            collection = db.collection(cls.COLLECTION_NAME)
            result = await collection.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "is_premium": True,
                        "premium_expires_at": expires_at,
                    }
                },
            )
            db_logger.info(f"Premium added to user {user_id} for {days} days")
            return result.modified_count > 0
        except Exception as e:
            db_logger.error(f"Error in add_premium: {e}")
            return False

    @classmethod
    async def remove_premium(cls, user_id: int) -> bool:
        """
        Remove premium from user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            bool: True if successful
        """
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            result = await collection.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "is_premium": False,
                        "premium_expires_at": None,
                    }
                },
            )
            db_logger.info(f"Premium removed from user {user_id}")
            return result.modified_count > 0
        except Exception as e:
            db_logger.error(f"Error in remove_premium: {e}")
            return False
