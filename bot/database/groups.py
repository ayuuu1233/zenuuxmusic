"""
Group database operations.
Manages group settings, statistics, and configurations.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List

from bot.database.mongodb import db
from bot.logger import db_logger


class GroupDB:
    """Handle group database operations."""

    COLLECTION_NAME = "groups"

    @classmethod
    async def init_indexes(cls) -> None:
        """Initialize database indexes for groups collection."""
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            await collection.create_index("group_id", unique=True)
            await collection.create_index("created_at")
            db_logger.info("Group indexes initialized")
        except Exception as e:
            db_logger.error(f"Failed to initialize group indexes: {e}")

    @classmethod
    async def get_or_create_group(
        cls,
        group_id: int,
        group_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get or create a group document.
        
        Args:
            group_id: Telegram group ID
            group_name: Group name (optional)
            
        Returns:
            Dict: Group document
        """
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            
            group = await collection.find_one({"group_id": group_id})
            
            if not group:
                group_doc = {
                    "group_id": group_id,
                    "group_name": group_name,
                    "created_at": datetime.utcnow(),
                    "is_blacklisted": False,
                    "is_music_disabled": False,
                    "admins": [],
                    "authorized_users": [],
                    "settings": {
                        "language": "en",
                        "repeat_mode": "off",  # off, one, all
                        "volume": 100,
                        "auto_delete_messages": True,
                    },
                    "statistics": {
                        "total_songs_played": 0,
                        "total_users": 0,
                        "total_duration": 0,
                    },
                }
                await collection.insert_one(group_doc)
                db_logger.info(f"Group {group_id} created")
                return group_doc
            
            return group
        except Exception as e:
            db_logger.error(f"Error in get_or_create_group: {e}")
            raise

    @classmethod
    async def get_group(cls, group_id: int) -> Optional[Dict[str, Any]]:
        """
        Get group document by ID.
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            Dict or None: Group document
        """
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            return await collection.find_one({"group_id": group_id})
        except Exception as e:
            db_logger.error(f"Error in get_group: {e}")
            return None

    @classmethod
    async def update_group(
        cls,
        group_id: int,
        update_data: Dict[str, Any],
    ) -> bool:
        """
        Update group document.
        
        Args:
            group_id: Telegram group ID
            update_data: Data to update
            
        Returns:
            bool: True if successful
        """
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            result = await collection.update_one(
                {"group_id": group_id},
                {"$set": update_data},
            )
            return result.modified_count > 0
        except Exception as e:
            db_logger.error(f"Error in update_group: {e}")
            return False

    @classmethod
    async def add_admin(cls, group_id: int, user_id: int) -> bool:
        """
        Add admin to group.
        
        Args:
            group_id: Telegram group ID
            user_id: User ID to add as admin
            
        Returns:
            bool: True if successful
        """
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            result = await collection.update_one(
                {"group_id": group_id},
                {"$addToSet": {"admins": user_id}},
            )
            db_logger.info(f"User {user_id} added as admin in group {group_id}")
            return result.modified_count > 0
        except Exception as e:
            db_logger.error(f"Error in add_admin: {e}")
            return False

    @classmethod
    async def remove_admin(cls, group_id: int, user_id: int) -> bool:
        """
        Remove admin from group.
        
        Args:
            group_id: Telegram group ID
            user_id: User ID to remove as admin
            
        Returns:
            bool: True if successful
        """
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            result = await collection.update_one(
                {"group_id": group_id},
                {"$pull": {"admins": user_id}},
            )
            db_logger.info(f"User {user_id} removed as admin from group {group_id}")
            return result.modified_count > 0
        except Exception as e:
            db_logger.error(f"Error in remove_admin: {e}")
            return False

    @classmethod
    async def is_admin(cls, group_id: int, user_id: int) -> bool:
        """
        Check if user is admin in group.
        
        Args:
            group_id: Telegram group ID
            user_id: User ID to check
            
        Returns:
            bool: True if admin
        """
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            group = await collection.find_one(
                {"group_id": group_id},
                {"admins": 1},
            )
            return user_id in group.get("admins", []) if group else False
        except Exception as e:
            db_logger.error(f"Error in is_admin: {e}")
            return False

    @classmethod
    async def is_music_disabled(cls, group_id: int) -> bool:
        """
        Check if music is disabled in group.
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            bool: True if music is disabled
        """
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            group = await collection.find_one(
                {"group_id": group_id},
                {"is_music_disabled": 1},
            )
            return group.get("is_music_disabled", False) if group else False
        except Exception as e:
            db_logger.error(f"Error in is_music_disabled: {e}")
            return False

    @classmethod
    async def is_blacklisted(cls, group_id: int) -> bool:
        """
        Check if group is blacklisted.
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            bool: True if blacklisted
        """
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            group = await collection.find_one(
                {"group_id": group_id},
                {"is_blacklisted": 1},
            )
            return group.get("is_blacklisted", False) if group else False
        except Exception as e:
            db_logger.error(f"Error in is_blacklisted: {e}")
            return False

    @classmethod
    async def blacklist_group(cls, group_id: int, reason: str = "") -> bool:
        """
        Blacklist a group.
        
        Args:
            group_id: Telegram group ID
            reason: Reason for blacklisting
            
        Returns:
            bool: True if successful
        """
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            result = await collection.update_one(
                {"group_id": group_id},
                {
                    "$set": {
                        "is_blacklisted": True,
                        "blacklist_reason": reason,
                        "blacklist_date": datetime.utcnow(),
                    }
                },
            )
            db_logger.info(f"Group {group_id} blacklisted: {reason}")
            return result.modified_count > 0
        except Exception as e:
            db_logger.error(f"Error in blacklist_group: {e}")
            return False

    @classmethod
    async def unblacklist_group(cls, group_id: int) -> bool:
        """
        Unblacklist a group.
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            bool: True if successful
        """
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            result = await collection.update_one(
                {"group_id": group_id},
                {
                    "$set": {"is_blacklisted": False},
                    "$unset": {"blacklist_reason": "", "blacklist_date": ""},
                },
            )
            db_logger.info(f"Group {group_id} unblacklisted")
            return result.modified_count > 0
        except Exception as e:
            db_logger.error(f"Error in unblacklist_group: {e}")
            return False

    @classmethod
    async def set_music_disabled(cls, group_id: int, disabled: bool) -> bool:
        """
        Enable/disable music in group.
        
        Args:
            group_id: Telegram group ID
            disabled: Whether to disable music
            
        Returns:
            bool: True if successful
        """
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            result = await collection.update_one(
                {"group_id": group_id},
                {"$set": {"is_music_disabled": disabled}},
            )
            return result.modified_count > 0
        except Exception as e:
            db_logger.error(f"Error in set_music_disabled: {e}")
            return False
