#! /usr/bin/env python3

import os
from pathlib import Path

from PIL import Image, ImageDraw

# Create a new image with a transparent background
size = 256
image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(image)

# Define colors
outer_color = (50, 70, 90)  # Dark blue-gray for the outer ring
inner_color = (100, 150, 200)  # Light blue for the inner circle (water)
bolt_color = (180, 160, 60)  # Brass color for bolts

# Draw the outer circle (porthole frame)
outer_radius = size // 2
draw.ellipse((0, 0, size - 1, size - 1), fill=outer_color)

# Draw the inner circle (glass/water)
inner_margin = size // 8
inner_pos = inner_margin
inner_size = size - (inner_margin * 2)
draw.ellipse(
    (inner_pos, inner_pos, inner_pos + inner_size - 1, inner_pos + inner_size - 1),
    fill=inner_color,
)

# Draw bolts around the porthole
bolt_radius = size // 16
bolt_positions = [
    (size // 4, size // 4),
    (size * 3 // 4, size // 4),
    (size // 4, size * 3 // 4),
    (size * 3 // 4, size * 3 // 4),
]

for pos in bolt_positions:
    draw.ellipse(
        (
            pos[0] - bolt_radius,
            pos[1] - bolt_radius,
            pos[0] + bolt_radius,
            pos[1] + bolt_radius,
        ),
        fill=bolt_color,
    )

static_dir = Path(__file__).parent.parent / "static"
# Save as PNG first
png_path = static_dir / "porthole.png"
image.save(str(png_path))

# Convert to different sizes for favicon.ico
sizes = [16, 32, 48, 64, 128, 256]
favicon_images = []

for s in sizes:
    resized_img = image.resize((s, s), Image.Resampling.LANCZOS)
    favicon_images.append(resized_img)

# Save as ICO
ico_path = static_dir / "favicon.ico"
favicon_images[0].save(
    str(ico_path),
    format="ICO",
    sizes=[(s, s) for s in sizes],
    append_images=favicon_images[1:],
)

print(f"Favicon created at {ico_path}")
print(f"PNG version created at {png_path}")
