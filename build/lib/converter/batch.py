"""Batch conversion across a directory tree, with optional parallelism."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
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


@dataclass
class _Job:
    """One unit of work: a source file and its destination."""
    src: Path
    dst: Path


def _collect_files(root: Path, extensions: set[str]) -> list[Path]:
    """Return every file under `root` whose suffix matches `extensions`."""
    return [
        p for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in extensions
    ]


def _output_path(src: Path, root: Path, out_dir: Path, new_suffix: str) -> Path:
    """Compute the output path, preserving relative structure under `root`."""
    relative = src.relative_to(root)
    return (out_dir / relative).with_suffix(new_suffix)


def _run_one(job: _Job, media_type: str,
             image_cfg: ImageConfig, audio_cfg: AudioConfig) -> bool:
    """Execute a single job. Returns True on success."""
    if media_type == "image":
        return convert_image(job.src, image_cfg, job.dst)
    return convert_audio(job.src, audio_cfg, job.dst)


def run_batch(
    src_dir: Path,
    out_dir: Path,
    media_type: str,
    image_cfg: ImageConfig,
    audio_cfg: AudioConfig,
    workers: int = 1,
) -> BatchResult:
    """Convert every compatible file under `src_dir` into `out_dir`.

    Uses up to `workers` threads in parallel. `workers=1` means serial.
    """
    result = BatchResult()

    # Make selections based on media type and carry out conversions of those files only 
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

    jobs = [
        _Job(src=src, dst=_output_path(src, src_dir, out_dir, new_suffix))
        for src in files
    ]

    log.info("found %d %s file(s) | using %d worker(s)",
             len(jobs), media_type, workers)

    # For single worker - run conversion of media in sync using this loop
    if workers <= 1:
        for job in jobs:
            if _run_one(job, media_type, image_cfg, audio_cfg):
                result.succeeded += 1
            else:
                result.failed += 1
        return result

    # For multiple workers, spawn the threads and run the conversion in parallel
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(_run_one, job, media_type, image_cfg, audio_cfg): job
            for job in jobs
        }
        for future in as_completed(futures):
            job = futures[future]
            try:
                ok = future.result()
            except Exception as exc:
                log.error("unexpected error on %s: %s", job.src.name, exc)
                ok = False
            # IMPORTANT: Make the updates on the main thread ONLY - don't update inside job runner - might be a race
            if ok:
                result.succeeded += 1
            else:
                result.failed += 1

    return result
