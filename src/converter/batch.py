"""Batch conversion across a directory tree."""

import logging
from dataclasses import dataclass
from pathlib import Path

from .audio import convert_audio
from .config import AudioConfig, ImageConfig
from .images import convert_image

log = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif", ".gif", ".ico", ".avif",
}

AUDIO_EXTENSIONS = {
    ".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a", ".opus", ".wma",
}


@dataclass
class BatchResult:
    """Summary of a batch run."""
    succeeded: int = 0
    failed: int = 0
    skipped: int = 0


def _collect_files(root: Path, extensions: set[str]) -> list[Path]:
    """Return every file under `root` whose suffix matches `extensions`."""
    return [
        p for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in extensions
    ]


def _output_path(src: Path, root: Path, out_dir: Path, new_suffix: str) -> Path:
    """Compute the output path, preserving the relative structure under `root`."""
    relative = src.relative_to(root)
    return (out_dir / relative).with_suffix(new_suffix)

def run_batch(
    src_dir: Path,
    out_dir: Path,
    media_type: str,
    image_cfg: ImageConfig,
    audio_cfg: AudioConfig,
) -> BatchResult:
    """Convert every compatible file under `src_dir` into `out_dir`."""
    result = BatchResult()

    if media_type == "image":
        extensions = IMAGE_EXTENSIONS
        new_suffix = f".{image_cfg.format.lower()}"
    else:
        extensions = AUDIO_EXTENSIONS
        new_suffix = f".{audio_cfg.format.lower()}"

    files = _collect_files(src_dir, extensions)
    if not files:
        log.warning("no %s files found under %s", media_type, src_dir)
        return result

    log.info("found %d %s file(s)", len(files), media_type)

    for src in files:
        dst = _output_path(src, src_dir, out_dir, new_suffix)

        if media_type == "image":
            ok = convert_image(src, image_cfg, dst)
        else:
            ok = convert_audio(src, audio_cfg, dst)

        if ok:
            result.succeeded += 1
        else:
            result.failed += 1

    return result
