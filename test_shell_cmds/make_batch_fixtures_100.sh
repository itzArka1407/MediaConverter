python - <<'EOF'
from pathlib import Path
from PIL import Image
import random

root = Path("sandbox/in")
random.seed(0)
for i in range(100):
    # 1600x1200 with noise so WebP has real work to do
    img = Image.new("RGB", (1600, 1200))
    px = img.load()
    for y in range(0, 1200, 4):
        for x in range(0, 1600, 4):
            c = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            for dy in range(4):
                for dx in range(4):
                    px[x+dx, y+dy] = c
    img.save(root / f"bulk_{i:03d}.png")
print("created 100 images")
EOF
