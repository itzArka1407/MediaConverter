"""Command-line interface for the media converter."""

import argparse
import logging
import os
import time
from pathlib import Path

from .metadata import get_version

from .audio import convert_audio
from .batch import run_batch, IMAGE_EXTENSIONS, AUDIO_EXTENSIONS
from .config import AudioConfig, ImageConfig
from .images import convert_image

log = logging.getLogger("converter")


def _parse_resize(value: str) -> tuple[int, int]:
    """Parse 'WxH' into a tuple of ints."""
    try:
        w, h = value.lower().split("x")
        return int(w), int(h)
    except (ValueError, AttributeError) as exc:
        raise argparse.ArgumentTypeError(
            f"invalid resize format: {value!r} (expected WxH, e.g. 1920x1080)"
        ) from exc


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    # Keep third-party libraries quiet even at DEBUG
    for noisy in ("PIL", "PIL.Image", "PIL.PngImagePlugin"):
        logging.getLogger(noisy).setLevel(logging.INFO)

def _infer_type(src: Path) -> str | None:
    """Get the type of media from the path"""
    suffix = src.suffix.lower()
    if suffix in IMAGE_EXTENSIONS:
        return "image"
    if suffix in AUDIO_EXTENSIONS:
        return "audio"
    return None

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="mediaconv",
        description="Convert images and audio between formats.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("input", type=Path, default=Path("."), help="input file or directory")
    p.add_argument("-o", "--output", type=Path, metavar="PATH",
                   help="output file (single input) or directory (batch input)")
    p.add_argument("--type", choices=["image", "audio", "all"], type=str.lower, default="all", help="The type of file for conversion:(default: all)")
    p.add_argument("--delete-original", action="store_true", default=False, help="Delete the original file after the conversion")
    p.add_argument("-v", "--verbose", action="store_true")
    p.add_argument(
        "--workers",
        type=int,
        metavar="N",
        default=os.cpu_count() or 1,
        help="number of parallel worker threads (default: CPU count)",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {get_version()}") # Version metadata

    img = p.add_argument_group("image options")
    img.add_argument("--image-format", default="WEBP", type=str.lower, metavar="FMT",
                     help="output image format (JPEG, PNG, WEBP, AVIF, ...)")
    img.add_argument("--quality", type=int, default=90, metavar="INT",
                     help="output image quality 1-100 for lossy formats")
    img.add_argument("--resize", type=_parse_resize, metavar="WxH",
                     help="resize output, e.g. 1920x1080")
    img.add_argument("--no-exif", action="store_true",
                     help="strip EXIF metadata from output")

    aud = p.add_argument_group("audio options")
    aud.add_argument("--audio-format", default="OPUS", type=str.lower, metavar="FMT",
                     help="output audio format (mp3, ogg, opus, flac, wav, ...)")
    aud.add_argument("--bitrate", default="256K",
                     help="bitrate for lossy formats, e.g. 192k")
    aud.add_argument("--sample-rate", type=int, metavar="HZ",
                     help="resample to this rate, e.g. 44100")
    aud.add_argument("--channels", type=int, choices=[1, 2],
                     help="1 for mono, 2 for stereo")
    aud.add_argument("--normalize", action="store_true",
                     help="apply EBU R128 loudness normalization (-14 LUFS)")

    return p

def path_kind(p: Path) -> str | None:
    """Find out the type of path for hte specified path: if a file or a dir"""
    if p.is_file():
        return "file"
    if p.is_dir():
        return "dir"
    return None

def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    _configure_logging(args.verbose)

    if args.workers < 1:
        log.error("--workers must be >= 1 (got %d)", args.workers)
        return 1

    # Check if the input is a file or directory
    ikind = path_kind(args.input)

    # Provide the necessary type(file/dir) and provide the output path for the conversion
    if ikind == "file":
        media_type = _infer_type(args.input)
        if media_type not in {"image", "audio"}:
            log.error("Cannot infer media type for: %s", args.input)
            return 1
        if args.type != "all" and args.type != media_type:
            log.error("--type %s doesn't match inferred type %s for %s",
                      args.type, media_type, args.input)
            return 1
        args.type = media_type # For a single file, get the concrete file type to perform further operations

        # No output is provided for the file input - generate the appropriate one
        if args.output is None:
            suffix = args.image_format.lower() if media_type == "image" else args.audio_format.lower()
            if not suffix.startswith("."):
                suffix = "." + suffix
            args.output = args.input.with_suffix(suffix)

    # If for a dir operation, the output is not provided, make it the same dir as the input
    if ikind == "dir" and args.output is None:
        args.output = args.input

    okind = path_kind(args.output)
    if okind is None or okind != ikind:
        log.error("Output type (%s) doesn't match input type (%s)", okind, ikind)
        return 1

    # The output and input cannot be the same file as of now
    if args.output.exists() and args.output.is_file() and args.input.samefile(args.output):
        log.error("The converter doesn't support rewriting the same file as of now")
        return 1

    # Build both configs once; batch and single-file paths share them.
    image_cfg = ImageConfig(
        format=args.image_format,
        quality=args.quality,
        resize=args.resize,
        keep_exif=not args.no_exif,
    )
    audio_cfg = AudioConfig(
        format=args.audio_format,
        bitrate=args.bitrate,
        sample_rate=args.sample_rate,
        channels=args.channels,
        normalize=args.normalize,
    )

    # Single file: direct conversion
    if ikind == "file":
        if args.type == "image":
            ok = convert_image(args.input, image_cfg, args.delete_original, args.output)
        else:
            ok = convert_audio(args.input, audio_cfg, args.delete_original, args.output)
        return 0 if ok else 1

    # Directory: batch (parallel if workers > 1)
    # For a strict type, only convert the type of file itself
    if args.type != "all":
        start = time.perf_counter()
        result = run_batch(
            args.input,
            args.output,
            args.type,
            image_cfg,
            audio_cfg,
            delete_original=args.delete_original,
            workers=args.workers,
        )
        elapsed = time.perf_counter() - start

        log.info(
            "batch complete: %d succeeded, %d failed in %.2fs",
            result.succeeded,
            result.failed,
            elapsed,
        )
        return 0 if result.failed == 0 else 1
    
    # For 'all' type, run both the batches of conversion of audio and images
    else:
        start1 = time.perf_counter()
        # Perform the conversion of the images
        result1 = run_batch(
            args.input,
            args.output,
            "image",
            image_cfg,
            audio_cfg,
            delete_original=args.delete_original,
            workers=args.workers,
        )
        elapsed1 = time.perf_counter() - start1

        start2 = time.perf_counter()
        # Perform the conversion of the audio files
        result2 = run_batch(
            args.input,
            args.output,
            "audio",
            image_cfg,
            audio_cfg,
            delete_original=args.delete_original,
            workers=args.workers,
        )
        elapsed2 = time.perf_counter() - start2

        # Log out the results
        log.info(
            "Image files' batch complete: %d succeeded, %d failed in %.2fs",
            result1.succeeded,
            result1.failed,
            elapsed1,
        )
        log.info(
            "Audio files' batch complete: %d succeeded, %d failed in %.2fs",
            result2.succeeded,
            result2.failed,
            elapsed2,
        )

        return 0 if result1.failed == 0 and result2.failed == 0 else 1

if __name__ == "__main__":
    raise SystemExit(main())
