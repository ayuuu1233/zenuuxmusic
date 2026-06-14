"""
Playlist database operations.
Manages user and group playlists.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pymongo import DESCENDING

from bot.database.mongodb import db
from bot.logger import db_logger


class PlaylistDB:
    """Handle playlist database operations."""

    COLLECTION_NAME = "playlists"

    @classmethod
    async def init_indexes(cls) -> None:
        """Initialize database indexes for playlists collection."""
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            await collection.create_index("playlist_id", unique=True)
            await collection.create_index("owner_id")
            await collection.create_index("group_id")
            await collection.create_index("created_at", direction=DESCENDING)
            db_logger.info("Playlist indexes initialized")
        except Exception as e:
            db_logger.error(f"Failed to initialize playlist indexes: {e}")

    @classmethod
    async def create_playlist(
        cls,
        playlist_id: str,
        owner_id: int,
        name: str,
        group_id: Optional[int] = None,
        description: str = "",
    ) -> Dict[str, Any]:
        """
        Create a new playlist.
        
        Args:
            playlist_id: Unique playlist ID
            owner_id: Owner's user ID
            name: Playlist name
            group_id: Group ID (optional for group playlists)
            description: Playlist description
            
        Returns:
            Dict: Created playlist document
        """
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            
            playlist_doc = {
                "playlist_id": playlist_id,
                "owner_id": owner_id,
                "group_id": group_id,
                "name": name,
                "description": description,
                "tracks": [],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            
            await collection.insert_one(playlist_doc)
            db_logger.info(f"Playlist {playlist_id} created by user {owner_id}")
            return playlist_doc
        except Exception as e:
            db_logger.error(f"Error in create_playlist: {e}")
            raise

    @classmethod
    async def get_playlist(cls, playlist_id: str) -> Optional[Dict[str, Any]]:
        """
        Get playlist by ID.
        
        Args:
            playlist_id: Playlist ID
            
        Returns:
            Dict or None: Playlist document
        """
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            return await collection.find_one({"playlist_id": playlist_id})
        except Exception as e:
            db_logger.error(f"Error in get_playlist: {e}")
            return None

    @classmethod
    async def get_user_playlists(cls, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all playlists owned by user.
        
        Args:
            user_id: User ID
            
        Returns:
            List: User's playlists
        """
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            return await collection.find(
                {"owner_id": user_id, "group_id": None}
            ).to_list(None)
        except Exception as e:
            db_logger.error(f"Error in get_user_playlists: {e}")
            return []

    @classmethod
    async def get_group_playlists(cls, group_id: int) -> List[Dict[str, Any]]:
        """
        Get all playlists for a group.
        
        Args:
            group_id: Group ID
            
        Returns:
            List: Group's playlists
        """
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            return await collection.find(
                {"group_id": group_id}
            ).to_list(None)
        except Exception as e:
            db_logger.error(f"Error in get_group_playlists: {e}")
            return []

    @classmethod
    async def add_track(
        cls,
        playlist_id: str,
        track_info: Dict[str, Any],
    ) -> bool:
        """
        Add track to playlist.
        
        Args:
            playlist_id: Playlist ID
            track_info: Track information dict with keys: title, url, duration, etc.
            
        Returns:
            bool: True if successful
        """
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            
            track = {
                "track_id": len((await cls.get_playlist(playlist_id)).get("tracks", [])),
                "title": track_info.get("title", "Unknown"),
                "url": track_info.get("url", ""),
                "duration": track_info.get("duration", 0),
                "artist": track_info.get("artist", "Unknown"),
                "thumbnail": track_info.get("thumbnail", ""),
                "added_at": datetime.utcnow(),
            }
            
            result = await collection.update_one(
                {"playlist_id": playlist_id},
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
    async def remove_track(cls, playlist_id: str, track_id: int) -> bool:
        """
        Remove track from playlist.
        
        Args:
            playlist_id: Playlist ID
            track_id: Track ID
            
        Returns:
            bool: True if successful
        """
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            result = await collection.update_one(
                {"playlist_id": playlist_id},
                {
                    "$pull": {"tracks": {"track_id": track_id}},
                    "$set": {"updated_at": datetime.utcnow()},
                },
            )
            return result.modified_count > 0
        except Exception as e:
            db_logger.error(f"Error in remove_track: {e}")
            return False

    @classmethod
    async def delete_playlist(cls, playlist_id: str) -> bool:
        """
        Delete a playlist.
        
        Args:
            playlist_id: Playlist ID
            
        Returns:
            bool: True if successful
        """
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            result = await collection.delete_one({"playlist_id": playlist_id})
            db_logger.info(f"Playlist {playlist_id} deleted")
            return result.deleted_count > 0
        except Exception as e:
            db_logger.error(f"Error in delete_playlist: {e}")
            return False

    @classmethod
    async def update_playlist_info(
        cls,
        playlist_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> bool:
        """
        Update playlist name and description.
        
        Args:
            playlist_id: Playlist ID
            name: New name (optional)
            description: New description (optional)
            
        Returns:
            bool: True if successful
        """
        try:
            update_data = {"updated_at": datetime.utcnow()}
            
            if name:
                update_data["name"] = name
            
            if description is not None:
                update_data["description"] = description
            
            collection = db.collection(cls.COLLECTION_NAME)
            result = await collection.update_one(
                {"playlist_id": playlist_id},
                {"$set": update_data},
            )
            
            return result.modified_count > 0
        except Exception as e:
            db_logger.error(f"Error in update_playlist_info: {e}")
            return False

    @classmethod
    async def get_playlist_size(cls, playlist_id: str) -> int:
        """
        Get number of tracks in playlist.
        
        Args:
            playlist_id: Playlist ID
            
        Returns:
            int: Number of tracks
        """
        try:
            playlist = await cls.get_playlist(playlist_id)
            return len(playlist.get("tracks", [])) if playlist else 0
        except Exception as e:
            db_logger.error(f"Error in get_playlist_size: {e}")
            return 0

    @classmethod
    async def clear_playlist(cls, playlist_id: str) -> bool:
        """
        Clear all tracks from playlist.
        
        Args:
            playlist_id: Playlist ID
            
        Returns:
            bool: True if successful
        """
        try:
            collection = db.collection(cls.COLLECTION_NAME)
            result = await collection.update_one(
                {"playlist_id": playlist_id},
                {
                    "$set": {
                        "tracks": [],
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
            return result.modified_count > 0
        except Exception as e:
            db_logger.error(f"Error in clear_playlist: {e}")
            return False
