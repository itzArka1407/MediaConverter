"""Configuration dataclasses for image and audio conversion"""

from dataclasses import dataclass

@dataclass(kw_only=True)
class ImageConfig:
    """Settings for image conversion"""
    format: str = "WEBP" # Default img codex
    quality: int = 80 # Default img quality
    resize: tuple[int,int]  | None = None # If some resize is being done on the file
    keep_exif: bool = True
    optimize: bool = True

@dataclass(kw_only=True)
class AudioConfig:
    """Settings for audio conversion."""
    format: str = "mp3"
    bitrate: str = "320k"
    sample_rate: int | None = None
    channels: int | None = None
    normalize: bool = False
