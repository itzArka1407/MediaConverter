#!/usr/bin/env bash
set -euo pipefail

ROOT="$(pwd)/sandbox"
rm -rf "$ROOT"
mkdir -p "$ROOT/in/a" "$ROOT/in/b" "$ROOT/out"

python - <<'EOF'
from pathlib import Path
from PIL import Image

root = Path("sandbox/in")

files = [
    root / "x1.png",
    root / "x2.png",
    root / "a" / "nested.png",
    root / "b" / "deep.png",
]

for path in files:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (300, 200), (100, 150, 200)).save(path)

# Decoy that should never be touched
(root / "notes.txt").write_text("ignore me")

# Corrupt file to test failure containment
(root / "broken.png").write_bytes(b"not an image")

# A valid audio file to test audio batching separately
EOF

# Generate a small audio test file via ffmpeg
ffmpeg -hide_banner -loglevel error \
    -f lavfi -i "sine=frequency=440:duration=1" \
    -c:a libmp3lame -b:a 128k \
    -y "$ROOT/in/tone.mp3"

echo "fixtures ready under sandbox/"
ls -R sandbox/in
