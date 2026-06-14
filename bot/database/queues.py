"""
Queue database operations.
Manages music queues for groups and persistence.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List

from bot.database.mongodb import db
from bot.logger import db_logger


class QueueDB:
    """Handle queue database operations."""

    COLLECTION_NAME = "queues"

    @classmethod
    async def init_indexes(cls) -> None:
        """Initialize database indexes for queues collection."""
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            await collection.create_index("group_id", unique=True)
            await collection.create_index("created_at")
            db_logger.info("Queue indexes initialized")
        except Exception as e:
            db_logger.error(f"Failed to initialize queue indexes: {e}")

    @classmethod
    async def get_or_create_queue(cls, group_id: int) -> Dict[str, Any]:
        """
        Get or create queue for group.
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            Dict: Queue document
        """
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            
            queue = await collection.find_one({"group_id": group_id})
            
            if not queue:
                queue_doc = {
                    "group_id": group_id,
                    "tracks": [],
                    "current_index": -1,
                    "is_playing": False,
                    "is_paused": False,
                    "loop_mode": "off",  # off, one, all
                    "volume": 100,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
                await collection.insert_one(queue_doc)
                db_logger.info(f"Queue created for group {group_id}")
                return queue_doc
            
            return queue
        except Exception as e:
            db_logger.error(f"Error in get_or_create_queue: {e}")
            raise

    @classmethod
    async def get_queue(cls, group_id: int) -> Optional[Dict[str, Any]]:
        """
        Get queue for group.
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            Dict or None: Queue document
        """
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            return await collection.find_one({"group_id": group_id})
        except Exception as e:
            db_logger.error(f"Error in get_queue: {e}")
            return None

    @classmethod
    async def add_track(
        cls,
        group_id: int,
        track_info: Dict[str, Any],
    ) -> bool:
        """
        Add track to queue.
        
        Args:
            group_id: Telegram group ID
            track_info: Track information
            
        Returns:
            bool: True if successful
        """
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            
            track = {
                "title": track_info.get("title", "Unknown"),
                "url": track_info.get("url", ""),
                "duration": track_info.get("duration", 0),
                "artist": track_info.get("artist", "Unknown"),
                "thumbnail": track_info.get("thumbnail", ""),
                "added_by": track_info.get("added_by", 0),
                "added_at": datetime.utcnow(),
            }
            
            result = await collection.update_one(
                {"group_id": group_id},
                {
                    "$push": {"tracks": track},
                    "$set": {"updated_at": datetime.utcnow()},
                },
            )
            
            return result.modified_count > 0
        except Exception as e:
            db_logger.error(f"Error in add_track: {e}")
            return False

    @classmethod
    async def remove_track(cls, group_id: int, track_index: int) -> bool:
        """
        Remove track from queue.
        
        Args:
            group_id: Telegram group ID
            track_index: Index of track to remove
            
        Returns:
            bool: True if successful
        """
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            queue = await cls.get_queue(group_id)
            
            if not queue or track_index >= len(queue.get("tracks", [])):
                return False
            
            tracks = queue["tracks"]
            tracks.pop(track_index)
            
            result = await collection.update_one(
                {"group_id": group_id},
                {
                    "$set": {
                        "tracks": tracks,
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
            
            return result.modified_count > 0
        except Exception as e:
            db_logger.error(f"Error in remove_track: {e}")
            return False

    @classmethod
    async def clear_queue(cls, group_id: int) -> bool:
        """
        Clear all tracks from queue.
        
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
                    "$set": {
                        "tracks": [],
                        "current_index": -1,
                        "is_playing": False,
                        "is_paused": False,
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
            
            return result.modified_count > 0
        except Exception as e:
            db_logger.error(f"Error in clear_queue: {e}")
            return False

    @classmethod
    async def get_queue_tracks(cls, group_id: int) -> List[Dict[str, Any]]:
        """
        Get all tracks in queue.
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            List: Queue tracks
        """
        try:
            queue = await cls.get_queue(group_id)
            return queue.get("tracks", []) if queue else []
        except Exception as e:
            db_logger.error(f"Error in get_queue_tracks: {e}")
            return []

    @classmethod
    async def get_current_track(cls, group_id: int) -> Optional[Dict[str, Any]]:
        """
        Get currently playing track.
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            Dict or None: Current track
        """
        try:
            queue = await cls.get_queue(group_id)
            if not queue:
                return None
            
            current_index = queue.get("current_index", -1)
            tracks = queue.get("tracks", [])
            
            if 0 <= current_index < len(tracks):
                return tracks[current_index]
            
            return None
        except Exception as e:
            db_logger.error(f"Error in get_current_track: {e}")
            return None

    @classmethod
    async def set_current_track(cls, group_id: int, index: int) -> bool:
        """
        Set currently playing track index.
        
        Args:
            group_id: Telegram group ID
            index: Track index
            
        Returns:
            bool: True if successful
        """
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            result = await collection.update_one(
                {"group_id": group_id},
                {
                    "$set": {
                        "current_index": index,
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
            
            return result.modified_count > 0
        except Exception as e:
            db_logger.error(f"Error in set_current_track: {e}")
            return False

    @classmethod
    async def set_playing_status(
        cls,
        group_id: int,
        is_playing: bool,
        is_paused: bool = False,
    ) -> bool:
        """
        Update playing status.
        
        Args:
            group_id: Telegram group ID
            is_playing: Whether music is playing
            is_paused: Whether music is paused
            
        Returns:
            bool: True if successful
        """
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            result = await collection.update_one(
                {"group_id": group_id},
                {
                    "$set": {
                        "is_playing": is_playing,
                        "is_paused": is_paused,
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
            
            return result.modified_count > 0
        except Exception as e:
            db_logger.error(f"Error in set_playing_status: {e}")
            return False

    @classmethod
    async def set_loop_mode(cls, group_id: int, mode: str) -> bool:
        """
        Set loop mode.
        
        Args:
            group_id: Telegram group ID
            mode: Loop mode (off, one, all)
            
        Returns:
            bool: True if successful
        """
        try:
            if mode not in ["off", "one", "all"]:
                return False
            
            collection = db.collection(cls.COLLECTION_NAME)
            result = await collection.update_one(
                {"group_id": group_id},
                {
                    "$set": {
                        "loop_mode": mode,
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
            
            return result.modified_count > 0
        except Exception as e:
            db_logger.error(f"Error in set_loop_mode: {e}")
            return False

    @classmethod
    async def set_volume(cls, group_id: int, volume: int) -> bool:
        """
        Set volume level.
        
        Args:
            group_id: Telegram group ID
            volume: Volume level (0-200)
            
        Returns:
            bool: True if successful
        """
        try:
            volume = max(0, min(200, volume))
            
            collection = db.collection(cls.COLLECTION_NAME)
            result = await collection.update_one(
                {"group_id": group_id},
                {
                    "$set": {
                        "volume": volume,
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
            
            return result.modified_count > 0
        except Exception as e:
            db_logger.error(f"Error in set_volume: {e}")
            return False

    @classmethod
    async def get_queue_size(cls, group_id: int) -> int:
        """
        Get number of tracks in queue.
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            int: Queue size
        """
        try:
            tracks = await cls.get_queue_tracks(group_id)
            return len(tracks)
        except Exception as e:
            db_logger.error(f"Error in get_queue_size: {e}")
            return 0

    @classmethod
    async def shuffle_queue(cls, group_id: int) -> bool:
        """
        Shuffle queue tracks.
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            bool: True if successful
        """
        try:
            import random
            
            queue = await cls.get_queue(group_id)
            if not queue:
                return False
            
            tracks = queue.get("tracks", [])
            if len(tracks) <= 1:
                return True
            
            # Keep current track, shuffle rest
            current_index = queue.get("current_index", 0)
            if current_index >= 0:
                current_track = tracks.pop(current_index)
                random.shuffle(tracks)
                tracks.insert(0, current_track)
                new_index = 0
            else:
                random.shuffle(tracks)
                new_index = -1
            
            collection = db.collection(cls.COLLECTION_NAME)
            result = await collection.update_one(
                {"group_id": group_id},
                {
                    "$set": {
                        "tracks": tracks,
                        "current_index": new_index,
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
            
            return result.modified_count > 0
        except Exception as e:
            db_logger.error(f"Error in shuffle_queue: {e}")
            return False
