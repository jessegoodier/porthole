#! /usr/bin/env python3

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Create a new image with a transparent background, wider to accommodate text
size = 256
text_space = 1450  # Additional width for text
image = Image.new("RGBA", (size + text_space, size), (0, 0, 0, 0))
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
font_size = 300
# Add text "Porthole" to the right of the image
font = ImageFont.truetype(
    "Copperplate.ttc",
    size=font_size,
)  # Adjust size to match visually

# Calculate text position (to the right of the porthole, vertically centered)
text = "Porthole"
text_position = (size + 10, (size - font_size) // 2)  # 10px padding from circle
draw.text(text_position, text, fill=outer_color, font=font)

static_dir = Path(__file__).parent.parent / "static"
# Save as PNG first
png_path = static_dir / "porthole-logo-with-text.png"
image.save(str(png_path))

print(f"PNG version created at {png_path}")
