"""Command-line interface for the media converter."""

import argparse
import logging
import os
from pathlib import Path

from .audio import convert_audio
from .config import AudioConfig, ImageConfig
from .images import convert_image
from .batch import run_batch

log = logging.getLogger("converter")

def _parse_resize(value: str) -> tuple[int, int]:
    """Produce appropriate resize value from the resizing string"""
    try:
        w, h = value.lower().split("x") # Split into 2 parts at 'x' - resize into those components
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
    # Discard logging from 3rd party libs during DEBUG
    for noisy in ("PIL", "PIL.image", "PIL.PngImagePlugin"):
        logging.getLogger(noisy).setLevel(logging.INFO)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="mediaconv",
        description="Convert images and audio between formats.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("input", type=Path, help="input file")
    p.add_argument("-o", "--output", type=Path, required=True, metavar="PATH", help="output file")
    p.add_argument("--type", choices=["image", "audio"], required=True)
    p.add_argument("-v", "--verbose", action="store_true")
    p.add_argument("--workers", type=int, metavar="N", help="No of worker threads in parallel: Default - no. of CPU cores", default=os.cpu_count() or 1)

    img = p.add_argument_group("image options")
    img.add_argument("--image-format", default="WEBP", metavar="FMT", help="The output image format: {JPEG, PNG, WEBP, etc..}")
    img.add_argument("--quality", type=int, default=90, metavar="INT", help="The output image quality: [1-100]")
    img.add_argument("--resize", type=_parse_resize, metavar="WxH", help="If the image dimensions are to be resized")
    img.add_argument("--no-exif", action="store_true", help="Strip EXIF metadata from the output image")

    aud = p.add_argument_group("audio options")
    aud.add_argument("--audio-format", default="mp3", metavar="FMT", help="Audio format of the output: {OGG, WAV, MP3, etc..}")
    aud.add_argument("--bitrate", default="320k", help="Bitrate of the output audio file")
    aud.add_argument("--sample-rate", type=int, metavar="HZ", help="Resampling audio to rate: e.g. 44100")
    aud.add_argument("--channels", type=int, choices=[1, 2], help="Mono(1) or Stereo(2)")
    aud.add_argument("--normalize", action="store_true", help="apply EBU R128 loudness normalization (-14 LUFS)")

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    _configure_logging(args.verbose)

    if not args.input.exists():
        log.error("input does not exist: %s", args.input)
        return 1

    # Build configs once; they're reused across all files in a batch
    if args.type == "image":
        image_cfg = ImageConfig(
            format=args.image_format,
            quality=args.quality,
            resize=args.resize,
            keep_exif=not args.no_exif,
        )
        audio_cfg = AudioConfig()   # unused, but required by run_batch signature
    else:
        audio_cfg = AudioConfig(
            format=args.audio_format,
            bitrate=args.bitrate,
            sample_rate=args.sample_rate,
            channels=args.channels,
            normalize=args.normalize,
        )
        image_cfg = ImageConfig()   # unused

    # Single file: convert directly
    if args.input.is_file():
        if args.type == "image":
            ok = convert_image(args.input, image_cfg, args.output)
        else:
            ok = convert_audio(args.input, audio_cfg, args.output)
        return 0 if ok else 1

    # Directory: batch
    result = run_batch(args.input, args.output, args.type, image_cfg, audio_cfg)
    log.info(
        "batch complete: %d succeeded, %d failed",
        result.succeeded, result.failed,
    )
    return 0 if result.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
