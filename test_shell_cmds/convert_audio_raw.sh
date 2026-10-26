python - <<'EOF'
from pathlib import Path
from converter.config import AudioConfig
from converter.audio import convert_audio

src = Path("./test_shell_cmds/aud_in.mp3")
OUTPUT_DIR = Path("./test_shell_cmds")

# MP3 → OGG
cfg = AudioConfig(format="ogg", bitrate="192k")
out = OUTPUT_DIR / "aud_out.ogg"
assert convert_audio(src, cfg, out), "ogg failed"
print("ogg size:", out.stat().st_size)

# MP3 → FLAC
cfg = AudioConfig(format="flac")
out = OUTPUT_DIR / "aud_out.flac"
assert convert_audio(src, cfg, out), "flac failed"
print("flac size:", out.stat().st_size)

# MP3 → stereo 48k WAV
cfg = AudioConfig(format="wav", sample_rate=48000, channels=2)
out = OUTPUT_DIR / "aud_out.wav"
assert convert_audio(src, cfg, out), "wav failed"
print("wav size:", out.stat().st_size)

# Inspect the WAV with ffprobe to confirm the settings took effect
import subprocess, json
probe = subprocess.run(
    ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", str(out)],
    capture_output=True, text=True,
)
info = json.loads(probe.stdout)
stream = info["streams"][0]
print("wav channels:", stream["channels"], "sample_rate:", stream["sample_rate"])
EOF
