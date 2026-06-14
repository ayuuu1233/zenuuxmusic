"""
Configuration module for Zenuux Music Bot.
Handles all environment variables and application settings.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project root directory
PROJECT_ROOT: Path = Path(__file__).parent

# ============================================================================
# TELEGRAM CONFIGURATION
# ============================================================================

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
"""Telegram Bot Token from BotFather"""

API_ID: int = int(os.getenv("API_ID", "0"))
"""Telegram API ID from my.telegram.org"""

API_HASH: str = os.getenv("API_HASH", "")
"""Telegram API Hash from my.telegram.org"""

OWNER_ID: int = int(os.getenv("OWNER_ID", "0"))
"""Bot Owner's Telegram User ID"""

BOT_SESSION_NAME: str = os.getenv("BOT_SESSION_NAME", "zenuuxmusic")
"""Session name for Pyrogram"""

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
"""MongoDB connection URI"""

MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "zenuuxmusic")
"""MongoDB database name"""

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_CHANNEL_ID: Optional[int] = (
    int(os.getenv("LOG_CHANNEL_ID")) if os.getenv("LOG_CHANNEL_ID") else None
)
"""Channel ID for bot logging and error reports"""

LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
"""Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"""

LOGS_DIR: Path = PROJECT_ROOT / "logs"
"""Directory for log files"""

# ============================================================================
# MUSIC & STREAMING CONFIGURATION
# ============================================================================

MAX_QUEUE_SIZE: int = int(os.getenv("MAX_QUEUE_SIZE", "100"))
"""Maximum number of tracks in queue per group"""

STREAM_QUALITY: str = os.getenv("STREAM_QUALITY", "480")
"""Default streaming quality (360p, 480p, 720p)"""

SEEK_STEP: int = int(os.getenv("SEEK_STEP", "5"))
"""Seek step in seconds"""

AUDIO_BITRATE: str = "192"
"""Audio bitrate in kbps"""

VIDEO_BITRATE: str = "2000"
"""Video bitrate in kbps"""

DEFAULT_VOLUME: int = 100
"""Default volume level (0-200)"""

# ============================================================================
# FEATURE TOGGLES
# ============================================================================

MAINTENANCE_MODE: bool = os.getenv("MAINTENANCE_MODE", "false").lower() == "true"
"""Enable maintenance mode (only owner can use bot)"""

ENABLE_PREMIUM: bool = os.getenv("ENABLE_PREMIUM", "true").lower() == "true"
"""Enable premium features"""

ENABLE_SEARCH: bool = os.getenv("ENABLE_SEARCH", "true").lower() == "true"
"""Enable YouTube search feature"""

ENABLE_PLAYLISTS: bool = os.getenv("ENABLE_PLAYLISTS", "true").lower() == "true"
"""Enable playlist management"""

# ============================================================================
# PERFORMANCE & LIMITS
# ============================================================================

MAX_SEARCH_RESULTS: int = 10
"""Maximum search results to return"""

SEARCH_TIMEOUT: int = 15
"""Timeout for YouTube search in seconds"""

EXTRACTION_TIMEOUT: int = 30
"""Timeout for media extraction in seconds"""

TEMP_DIR: Path = PROJECT_ROOT / "temp"
"""Temporary directory for downloaded files"""

MAX_FILE_SIZE: int = 2147483648  # 2GB
"""Maximum file size for streaming"""

CLEANUP_INTERVAL: int = 3600
"""Auto cleanup interval in seconds (1 hour)"""

# ============================================================================
# RATE LIMITING & ANTI-SPAM
# ============================================================================

FLOOD_WAIT_DURATION: int = 5
"""Duration to wait when flood wait is triggered (seconds)"""

USER_COOLDOWN: dict[str, int] = {
    "play": 2,
    "search": 3,
    "skip": 1,
    "pause": 1,
}
"""Command cooldowns per user (seconds)"""

MAX_QUEUE_PER_USER: int = 50
"""Maximum tracks per user in queue"""

# ============================================================================
# PATHS & DIRECTORIES
# ============================================================================

# Create necessary directories
LOGS_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

DOWNLOADS_DIR: Path = TEMP_DIR / "downloads"
"""Directory for downloaded audio/video files"""

THUMBNAILS_DIR: Path = TEMP_DIR / "thumbnails"
"""Directory for cached thumbnails"""

DOWNLOADS_DIR.mkdir(exist_ok=True)
THUMBNAILS_DIR.mkdir(exist_ok=True)

# ============================================================================
# YT-DLP CONFIGURATION
# ============================================================================

YTDLP_OPTS: dict = {
    "format": "bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch",
    "socket_timeout": 30,
    "extractor_args": {"youtube": {"player_client": ["web"]}},
    "http_headers": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    },
}
"""yt-dlp configuration options"""

# ============================================================================
# VALIDATION
# ============================================================================

def validate_config() -> bool:
    """
    Validate critical configuration settings.
    
    Returns:
        bool: True if all required configs are valid
        
    Raises:
        ValueError: If critical configuration is missing
    """
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is not set in environment variables")
    
    if not API_ID or API_ID == 0:
        raise ValueError("API_ID is not set in environment variables")
    
    if not API_HASH:
        raise ValueError("API_HASH is not set in environment variables")
    
    if not OWNER_ID or OWNER_ID == 0:
        raise ValueError("OWNER_ID is not set in environment variables")
    
    return True
