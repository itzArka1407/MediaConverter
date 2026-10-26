"""Audio conversion using ffmpeg via subprocess."""

import logging
import subprocess
from pathlib import Path

from .helpers import DEV_MODE

from .deletion import delete_file

from .config import AudioConfig

log = logging.getLogger(__name__)

# (output format: ffmpeg encoder name) -- To perform the encoding based on the extension
AUDIO_CODECS: dict[str, str] = {
    "mp3":  "libmp3lame",
    "ogg":  "libvorbis",
    "opus": "libopus",
    "flac": "flac",
    "wav":  "pcm_s16le",
    "aac":  "aac",
    "m4a":  "aac",
    "wma":  "wmav2",
}

# Formats that accept a bitrate parameter
LOSSY_FORMATS = {"mp3", "ogg", "opus", "aac", "m4a", "wma"}

def _build_command(src: Path, cfg: AudioConfig, dst: Path) -> list[str]:
    """Assemble the ffmpeg argument list from a config."""
    fmt = cfg.format.lower()

    cmd: list[str] = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "error",
        "-y",                       # overwrite output without asking
        "-i", str(src),
    ]

    codec = AUDIO_CODECS.get(fmt)
    if codec is not None:
        cmd += ["-c:a", codec]

    if fmt in LOSSY_FORMATS:
        cmd += ["-b:a", cfg.bitrate]

    if cfg.sample_rate is not None:
        cmd += ["-ar", str(cfg.sample_rate)]

    if cfg.channels is not None:
        cmd += ["-ac", str(cfg.channels)]

    if cfg.normalize:
        # EBU R128 loudness normalization targeting -14 LUFS
        cmd += ["-af", "loudnorm=I=-14:TP=-1.5:LRA=11"]

    cmd.append(str(dst))
    return cmd


def convert_audio(src: Path, cfg: AudioConfig, delete_original: bool, dst: Path | None = None) -> bool:
    """Convert an audio file by invoking ffmpeg."""
    if dst is None:
        dst = src.with_suffix(f".{cfg.format.lower()}")

    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = _build_command(src, cfg, dst)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        log.error("ffmpeg not found on PATH. Install it and retry.")
        return False

    if result.returncode != 0:
        log.error("Audio failed %s:\n%s", src.name, result.stderr.strip())
        return False

    log.info("Audio: %s => %s", src.name, dst.name)
    # Delete the original file if the user specifies
    if delete_original:
        delete_file(src=src, dry_run=DEV_MODE)
    return True

