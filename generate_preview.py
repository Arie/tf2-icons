#!/usr/bin/env python3
"""
Generate a preview image showing weapon names and their icons
"""

import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def parse_css_positions(css_path: Path):
    """Parse the CSS file to extract weapon positions"""
    content = css_path.read_text()

    weapons = {}

    # Match .killicon-{name} blocks
    pattern = r'\.killicon-([a-z0-9_\-]+)\s*\{[^}]*width:\s*(\d+)px;[^}]*height:\s*(\d+)px;[^}]*background-position:\s*-(\d+)px\s*-(\d+)px;'

    for match in re.finditer(pattern, content):
        weapon_name = match.group(1)
        width = int(match.group(2))
        height = int(match.group(3))
        x = int(match.group(4))
        y = int(match.group(5))

        weapons[weapon_name] = (x, y, width, height)

    print(f"Parsed {len(weapons)} weapon icons from CSS")
    return weapons


def create_preview_image(sprite_path: Path, css_path: Path, weapon_list: list, output_path: Path, show_all: bool = False):
    """Create a preview image with weapon names and icons"""

    # Load sprite sheet
    sprite = Image.open(sprite_path)

    # Parse CSS positions
    positions = parse_css_positions(css_path)

    if show_all:
        # Show all weapons from CSS
        weapons_to_show = list(positions.keys())
        print(f"Showing all {len(weapons_to_show)} weapons from CSS")
    else:
        # Filter weapon list to only those we have icons for
        weapons_to_show = []
        missing = []
        for weapon in weapon_list:
            if weapon in positions:
                weapons_to_show.append(weapon)
            else:
                missing.append(weapon)

        print(f"Found {len(weapons_to_show)} weapons with icons")
        if missing:
            print(f"Missing {len(missing)} weapons: {', '.join(missing[:10])}")

    # Sort weapons alphabetically
    weapons_to_show.sort()

    # Calculate image dimensions
    row_height = 40
    num_weapons = len(weapons_to_show)
    img_width = 800
    img_height = num_weapons * row_height + 100  # Extra space for header

    # Create image
    img = Image.new('RGB', (img_width, img_height), color='#1e1e1e')
    draw = ImageDraw.Draw(img)

    # Try to use a monospace font, fallback to default
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 14)
        header_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', 16)
    except:
        font = ImageFont.load_default()
        header_font = font

    # Draw header
    draw.text((20, 20), "Weapon Name", fill='#ffffff', font=header_font)
    draw.text((400, 20), "Icon", fill='#ffffff', font=header_font)
    draw.line([(10, 50), (img_width - 10, 50)], fill='#666666', width=1)

    # Draw each weapon
    y_offset = 60

    for weapon in weapons_to_show:
        x, y, w, h = positions[weapon]

        # Draw weapon name
        draw.text((20, y_offset + (row_height - 16) // 2), weapon, fill='#cccccc', font=font)

        # Extract and paste icon
        icon = sprite.crop((x, y, x + w, y + h))

        # Center icon vertically in the row
        icon_y = y_offset + (row_height - h) // 2
        img.paste(icon, (400, icon_y), icon if icon.mode == 'RGBA' else None)

        # Draw separator line
        draw.line([(10, y_offset + row_height - 1), (img_width - 10, y_offset + row_height - 1)],
                  fill='#333333', width=1)

        y_offset += row_height

    # Save image
    img.save(output_path, 'PNG')
    print(f"Preview saved to {output_path}")
    print(f"Image size: {img_width}x{img_height}")


def main():
    import sys

    sprite_path = Path('dist/killicons.webp')
    css_path = Path('dist/killicons.css')
    output_path = Path('dist/killicons_preview.png')
    weapons_file = Path('weapons.txt')

    # Check if --all flag is passed
    show_all = '--all' in sys.argv

    # Read weapon list from weapons.txt if it exists
    if weapons_file.exists():
        weapon_list = [w.strip() for w in weapons_file.read_text().strip().split('\n') if w.strip()]
        print(f"Loaded {len(weapon_list)} weapons from {weapons_file}")
    else:
        # Fallback to empty list (will show all)
        weapon_list = []
        show_all = True
        print("No weapons.txt found, showing all weapons")

    create_preview_image(sprite_path, css_path, weapon_list, output_path, show_all=show_all)


if __name__ == '__main__':
    main()
