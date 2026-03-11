"""
Run once to generate icon.png for the menu bar app.
Produces a monochrome 22x22 clock template icon (auto-adapts to dark/light mode).
"""
import math
from PIL import Image, ImageDraw

SIZE = 22
cx, cy = SIZE // 2, SIZE // 2


def draw_clock(path: str) -> None:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Clock face circle
    m = 1
    draw.ellipse([m, m, SIZE - m - 1, SIZE - m - 1], outline=(0, 0, 0, 255), width=2)

    # Hour hand — pointing to ~10
    hour_angle = math.radians(-60)  # 10 o'clock
    hlen = 4
    draw.line(
        [cx, cy, cx + hlen * math.sin(hour_angle), cy - hlen * math.cos(hour_angle)],
        fill=(0, 0, 0, 255),
        width=2,
    )

    # Minute hand — pointing to ~2
    min_angle = math.radians(60)  # 2 o'clock
    mlen = 6
    draw.line(
        [cx, cy, cx + mlen * math.sin(min_angle), cy - mlen * math.cos(min_angle)],
        fill=(0, 0, 0, 255),
        width=2,
    )

    # Centre dot
    draw.ellipse([cx - 1, cy - 1, cx + 1, cy + 1], fill=(0, 0, 0, 255))

    img.save(path)
    print(f"✅ Saved {path}")


if __name__ == "__main__":
    draw_clock("icon.png")
