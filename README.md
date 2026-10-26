# MediaConverter

A command-line tool to convert images and audio files between formats - one file at a time, or a whole directory in parallel.

## Features

- Convert a single image or audio file to another format.
- Batch-convert an entire directory (with parallel workers).
- Smart defaults: infer the media type from the input and derive the output path from the input's suffix.
- Optional metadata handling (keep or strip EXIF).
- Image resizing, audio bitrate / sample-rate / channel control.
- Optional deletion of source files after a successful conversion.

## Requirements

**Important:** MediaConverter requires **FFmpeg** to be installed on your machine and available on your `PATH`. Audio conversion (and some image operations) will not work without it.

Install FFmpeg for your platform:

- macOS (Homebrew): `brew install ffmpeg`
- Ubuntu/Debian: `sudo apt update && sudo apt install ffmpeg`
- Fedora: `sudo dnf install ffmpeg`
- Windows (Scoop): `scoop install ffmpeg` - or download from https://ffmpeg.org/download.html and add the `bin` folder to your `PATH`

Verify it's available:

```bash
ffmpeg -version
```

If that command prints a version, you're good to go.

You also need **Python 3.10+**.

## Installation

### Recommended: pipx (isolated, global command)

```bash
# Install pipx if you don't have it
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Install MediaConverter from a local checkout
cd /path/to/MediaConverter
pipx install .
```

After this, the `mediaconv` command is available anywhere in your shell.

To reinstall after pulling changes:

```bash
pipx install . --force
```

### Alternative: virtual environment (for development)

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e .
```

## Usage

```bash
mediaconv [OPTIONS] INPUT
```

`INPUT` may be a **file** or a **directory**. If you don't pass `--output`, the output path is inferred:

- **File input:** same name, new suffix based on the target format.
- **Directory input:** files are converted in place (in the same directory).

### Examples

Convert a single image to WebP:

```bash
mediaconv photo.png --image-format webp
```

Convert an audio file to MP3:

```bash
mediaconv track.flac --audio-format mp3 --bitrate 256k
```

Batch-convert a directory using 4 parallel workers:

```bash
mediaconv music/ --type audio --audio-format mp3 --workers 4
```

Convert an image, resize it, and strip EXIF:

```bash
mediaconv shot.jpg --image-format png --resize 1280x720 --no-exif
```

Write to an explicit output path:

```bash
mediaconv input.png --output out/result.webp --image-format webp
```

### Options

| Option | Description |
|---|---|
| `-h, --help` | Show help and exit. |
| `-v, --verbose` | Increase log verbosity (repeatable). |
| `-t, --type TYPE` | Force media type: `image` or `audio` (case-insensitive). Required for directory conversion. |
| `--image-format FMT` | Target image format (e.g. `png`, `jpeg`, `webp`). |
| `--audio-format FMT` | Target audio format (e.g. `mp3`, `flac`, `ogg`). |
| `--quality N` | Encoder quality, 0–100. |
| `--bitrate RATE` | Audio bitrate (e.g. `192k`, `256k`). |
| `--sample-rate HZ` | Audio sample rate. |
| `--channels N` | Number of audio channels. |
| `--resize WxH` | Resize images to the given dimensions. |
| `--no-exif` | Strip EXIF metadata from images. |
| `--delete-original` | Delete each source file after a successful conversion. |
| `-w, --workers N` | Parallel workers for directory conversion (must be ≥ 1). |
| `--output PATH` | Explicit output path. |

### Exit status

- `0` - all conversions succeeded.
- `1` - one or more conversions failed, or arguments were invalid.

## Notes and caveats

- `--delete-original` is destructive. Files are only deleted after their conversion succeeds, but there is no undo. Consider running on a copy first if you're unsure.
- In-place conversion of a file onto itself is currently not supported; the tool will refuse rather than risk corrupting the source.
- Some formats cannot store alpha channels; transparent regions are flattened onto white when converting to formats like JPEG.
- Directory conversion requires an explicit `--type` so the tool knows which files to pick up.

## Man page

If installed with pipx, a man page is available:

```bash
man mediaconv
```

## License

Licensed under the **Apache License 2.0**. See the `LICENSE` file for the full text, or read it at https://www.apache.org/licenses/LICENSE-2.0.

## Contributing

Issues and pull requests are welcome. Please make sure `ffmpeg` is available in your development environment before running the test suite.
