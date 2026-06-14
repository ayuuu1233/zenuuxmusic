"""
YouTube search and music extraction utilities using yt-dlp.
Handles searching, extracting metadata, and downloading audio/video.
"""

import asyncio
import re
from typing import Optional, Dict, Any, List
from pathlib import Path
import yt_dlp
from datetime import datetime

import config
from bot.logger import music_logger


class MusicExtractor:
    """Extract music information from YouTube and other sources."""

    @staticmethod
    async def extract_info(
        query: str,
        is_playlist: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Extract information about a video or playlist.
        
        Args:
            query: YouTube URL or search query
            is_playlist: Whether to extract playlist info
            
        Returns:
            Dict or None: Extracted information
        """
        try:
            loop = asyncio.get_event_loop()
            
            ydl_opts = {
                **config.YTDLP_OPTS,
                "socket_timeout": config.EXTRACTION_TIMEOUT,
                "quiet": True,
                "no_warnings": True,
            }
            
            if is_playlist:
                ydl_opts["extract_flat"] = "in_playlist"
                ydl_opts["playlist_items"] = "1-50"
            
            def _extract() -> Dict[str, Any]:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(query, download=False)
                    return info
            
            info = await asyncio.wait_for(
                loop.run_in_executor(None, _extract),
                timeout=config.EXTRACTION_TIMEOUT,
            )
            return info
        except asyncio.TimeoutError:
            music_logger.error(f"Extraction timeout for query: {query}")
            return None
        except Exception as e:
            music_logger.error(f"Error extracting info for {query}: {e}")
            return None

    @staticmethod
    async def search_youtube(
        query: str,
        max_results: int = config.MAX_SEARCH_RESULTS,
    ) -> List[Dict[str, Any]]:
        """
        Search YouTube for videos.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List: Search results with metadata
        """
        try:
            loop = asyncio.get_event_loop()
            
            ydl_opts = {
                **config.YTDLP_OPTS,
                "extract_flat": "in_playlist",
                "playlistend": max_results,
                "quiet": True,
                "no_warnings": True,
            }
            
            def _search() -> List[Dict[str, Any]]:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    results = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
                    return results.get("entries", [])
            
            results = await asyncio.wait_for(
                loop.run_in_executor(None, _search),
                timeout=config.SEARCH_TIMEOUT,
            )
            
            # Format results
            formatted_results = []
            for item in results:
                formatted_results.append({
                    "id": item.get("id", ""),
                    "title": item.get("title", "Unknown"),
                    "url": f"https://www.youtube.com/watch?v={item.get('id', '')}",
                    "duration": item.get("duration", 0),
                    "thumbnail": item.get("thumbnail", ""),
                    "uploader": item.get("uploader", "Unknown"),
                    "view_count": item.get("view_count", 0),
                })
            
            return formatted_results
        except asyncio.TimeoutError:
            music_logger.error(f"Search timeout for query: {query}")
            return []
        except Exception as e:
            music_logger.error(f"Error searching YouTube: {e}")
            return []

    @staticmethod
    async def get_audio_url(
        url: str,
    ) -> Optional[str]:
        """
        Get direct audio stream URL.
        
        Args:
            url: YouTube URL
            
        Returns:
            str or None: Direct audio stream URL
        """
        try:
            loop = asyncio.get_event_loop()
            
            ydl_opts = {
                **config.YTDLP_OPTS,
                "format": "bestaudio/best",
                "quiet": True,
                "no_warnings": True,
            }
            
            def _get_url() -> Optional[str]:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    return info.get("url") or info.get("formats", [{}])[0].get("url")
            
            audio_url = await asyncio.wait_for(
                loop.run_in_executor(None, _get_url),
                timeout=config.EXTRACTION_TIMEOUT,
            )
            return audio_url
        except asyncio.TimeoutError:
            music_logger.error(f"URL extraction timeout for: {url}")
            return None
        except Exception as e:
            music_logger.error(f"Error getting audio URL: {e}")
            return None

    @staticmethod
    async def get_video_url(
        url: str,
        quality: str = "480",
    ) -> Optional[str]:
        """
        Get direct video stream URL.
        
        Args:
            url: YouTube URL
            quality: Video quality (360p, 480p, 720p)
            
        Returns:
            str or None: Direct video stream URL
        """
        try:
            loop = asyncio.get_event_loop()
            
            # Map quality to yt-dlp format
            quality_map = {
                "360": "bestvideo[height<=360]+bestaudio/best",
                "480": "bestvideo[height<=480]+bestaudio/best",
                "720": "bestvideo[height<=720]+bestaudio/best",
            }
            
            format_str = quality_map.get(quality, "bestvideo+bestaudio/best")
            
            ydl_opts = {
                **config.YTDLP_OPTS,
                "format": format_str,
                "quiet": True,
                "no_warnings": True,
            }
            
            def _get_url() -> Optional[str]:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    return info.get("url") or info.get("formats", [{}])[0].get("url")
            
            video_url = await asyncio.wait_for(
                loop.run_in_executor(None, _get_url),
                timeout=config.EXTRACTION_TIMEOUT,
            )
            return video_url
        except asyncio.TimeoutError:
            music_logger.error(f"Video URL extraction timeout for: {url}")
            return None
        except Exception as e:
            music_logger.error(f"Error getting video URL: {e}")
            return None

    @staticmethod
    async def get_track_info(url: str) -> Optional[Dict[str, Any]]:
        """
        Get complete track information.
        
        Args:
            url: YouTube URL or search query
            
        Returns:
            Dict or None: Track information
        """
        try:
            info = await MusicExtractor.extract_info(url)
            
            if not info:
                # Try searching if direct extraction fails
                search_results = await MusicExtractor.search_youtube(url, max_results=1)
                if search_results:
                    return search_results[0]
                return None
            
            return {
                "id": info.get("id", ""),
                "title": info.get("title", "Unknown"),
                "url": info.get("webpage_url", url),
                "duration": info.get("duration", 0),
                "thumbnail": info.get("thumbnail", ""),
                "artist": info.get("uploader", "Unknown"),
                "view_count": info.get("view_count", 0),
                "upload_date": info.get("upload_date", ""),
                "description": info.get("description", ""),
            }
        except Exception as e:
            music_logger.error(f"Error getting track info: {e}")
            return None

    @staticmethod
    def is_youtube_url(url: str) -> bool:
        """
        Check if URL is a YouTube URL.
        
        Args:
            url: URL to check
            
        Returns:
            bool: True if YouTube URL
        """
        youtube_regex = (
            r"(https?://)?(www\.)?"
            r"(youtube|youtu|youtube-nocookie)"
            r"(\.|\.com)"
        )
        return bool(re.match(youtube_regex, url))

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """
        Check if URL is valid.
        
        Args:
            url: URL to check
            
        Returns:
            bool: True if valid URL
        """
        url_pattern = re.compile(
            r"^https?://"
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"
            r"localhost|"
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
            r"(?::\d+)?"
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE
        )
        return bool(url_pattern.match(url))
