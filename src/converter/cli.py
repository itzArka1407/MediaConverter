"""Command-line interface for the media converter."""

import argparse
import logging
from pathlib import Path

from .audio import convert_audio
from .config import AudioConfig, ImageConfig
from .images import convert_image

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

    if args.type == "image":
        image_cfg = ImageConfig(
            format=args.image_format,
            quality=args.quality,
            resize=args.resize,
            keep_exif=not args.no_exif,
        )
        ok = convert_image(args.input, image_cfg, args.output)
    else:
        audio_cfg = AudioConfig(
            format=args.audio_format,
            bitrate=args.bitrate,
            sample_rate=args.sample_rate,
            channels=args.channels,
            normalize=args.normalize,
        )
        ok = convert_audio(args.input, audio_cfg, args.output)

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
