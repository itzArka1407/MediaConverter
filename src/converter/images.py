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
        with Image.open(src) as img:
            target = cfg.format.upper() # Check the conversion format

            if target not in SUPPORTED_FORMATS:
                log.error("unsupported image format: %s", target)
                return False

            # Grab metadata before any mode conversion
            exif = img.info.get("exif") if cfg.keep_exif else None
            icc = img.info.get("icc_profile")

            # Flatten alpha for formats that can't store it
            if target in NO_ALPHA_FORMATS and img.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                img = img.convert("RGBA")
                # For mask: at alpha places, convert it to white pixels(taken from background above which is a white image basically)
                # For opaque pixels, take it from image itself
                background.paste(img, mask=img.split()[-1])
                img = background
            elif img.mode == "P" and target not in {"GIF", "PNG"}:
                img = img.convert("RGB")

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
