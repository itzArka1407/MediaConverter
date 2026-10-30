"""Image conversion to optimized format"""

import logging
from pathlib import Path

from PIL import Image

from converter.deletion import delete_file
from .helpers import DEV_MODE

from .config import ImageConfig

log = logging.getLogger(__name__)

# Formats that can be converted to
SUPPORTED_FORMATS = {
    "JPEG", "JPG", "PNG", "WEBP", "BMP", "TIFF", "GIF", "ICO", "AVIF",
}

# Formats without any alpha - transparency is lost
NO_ALPHA_FORMATS = {"JPEG", "JPG", "BMP"}

def convert_image(src: Path, cfg: ImageConfig, delete_original: bool, dst: Path | None = None) -> bool:
    """Convert an image from src to dst using the given config."""
    if dst is None:
        dst = src.with_suffix(f".{cfg.format}")

    try:
        with Image.open(src).convert("RGBA") as img:
            target = cfg.format.upper() # Check the conversion format

            if target not in SUPPORTED_FORMATS:
                log.error("unsupported image format: %s", target)
                return False

            # Grab metadata before any mode conversion
            exif = img.info.get("exif") if cfg.keep_exif else None
            icc = img.info.get("icc_profile")

            # If user has defined an overlay
            if cfg.rgba_overlay is not None:
                overlay = Image.new("RGBA", img.size, cfg.rgba_overlay)
                img = Image.alpha_composite(img, overlay)

            # When converting an alpha img to non-alpha img, fill up gaps
            # TODO: For now, this is only making it white, later, make it user-defined
            if target in NO_ALPHA_FORMATS:
            # If image is totally opaque(just the format supports alpha)
                if img.getchannel("A").getextrema() == (255, 255):
                    img = img.convert("RGB")            # opaque everywhere → cheap path
                else:
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])
                    img = background

            # Resize using high-quality Lanczos
            if cfg.resize is not None:
                img = img.resize(cfg.resize, Image.Resampling.LANCZOS) 

            # Build save() kwargs based on target format
            save_kwargs: dict[str, object] = {}

            if target in {"JPEG", "JPG", "WEBP", "AVIF"}:
                save_kwargs["quality"] = cfg.quality
                save_kwargs["optimize"] = cfg.optimize

            if target in {"JPEG", "JPG"}:
                save_kwargs["progressive"] = True

            if exif is not None and target in {"JPEG", "JPG", "WEBP", "TIFF"}:
                save_kwargs["exif"] = exif

            if icc is not None:
                save_kwargs["icc_profile"] = icc

            # Make output dir if not exists to store the file
            dst.parent.mkdir(parents=True, exist_ok=True)

            img.save(dst, format=target, **save_kwargs)

        log.info("Image: %s -> %s", src.name, dst.name)

        # Delete the original file if the user instructs to
        if delete_original:
            delete_file(src=src, dry_run=DEV_MODE)
        return True

    except FileNotFoundError:
        log.error("Image not found: %s", src)
        return False
    except Exception as exc:
        log.error("Image failed %s: %s", src.name, exc)
        return False
