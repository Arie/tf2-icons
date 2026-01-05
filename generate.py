#!/usr/bin/env python3
"""
TF2 Killicons Sprite Generator

Extracts killicons from TF2 VPK files and generates an optimized sprite sheet with CSS.

"""

import io
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import vpk
from PIL import Image
from srctools.vtf import VTF


# Known mismatches between log line names and TF2 internal names
WEAPON_MAPPINGS = {
    'robot_arm': 'robot_arm_kill',
    'unique_pickaxe': 'pickaxe',
    'world': 'skull',
    'trigger_hurt': 'skull',
    'env_explosion': 'skull',
    'player': 'skull',
    'tf_pumpkin_bomb': 'pumpkindeath',
    # Community mod sprites (telefrag, tf_projectile_*, entity_medigun_shield are in community mod)
    # 'default' uses saw_kill icon
    'default': 'saw_kill',
    # Additional mappings based on TF2 internal names
    'grenadelauncher': 'tf_projectile_pipe',
    'rocketlauncher': 'tf_projectile_rocket',
    'stickybomb_launcher': 'tf_projectile_pipe_remote',
    'flamethrower': 'tf_weapon_flamethrower',
    'knife': 'tf_weapon_knife',
    # _kill suffix weapons
    'frontier_justice': 'frontier_kill',
    'southern_hospitality': 'southern_comfort_kill',
    'golden_wrench': 'wrench_golden',
    'gunslinger': 'robot_arm_kill',
    'jag': 'wrench_jag',
    'wrangler': 'wrangler_kill',
    # Demoman shields
    'chargin_targe': 'demoshield',
    'loose_cannon': 'loose_cannon_impact',
    # Community weapons
    'tf_projectile_mechanicalarmorb': 'tf_projectile_mechanicalarmor',
    # Scout weapons
    'baby_face_blaster': 'pep_brawlerblaster',
    'winger': 'the_winger',
    'pretty_boy_pocket_pistol': 'pep_pistol',
    'flying_guillotine': 'guillotine',
    'three_rune_blade': 'boston_basher',
    'sun_on_a_stick': 'lava_bat',
    'fan_o_war': 'warfan',
    # Soldier weapons
    'black_box': 'blackbox',
    'beggars_bazooka': 'dumpster_device',
    'beggar': 'dumpster_device',
    'direct_hit': 'rocketlauncher_directhit',
    'original': 'quake_rl',
    'escape_plan': 'pickaxe',
    'equalizer': 'pickaxe',
    'unique_pickaxe_escape': 'pickaxe',
    # Pyro weapons
    'dragon_fury': 'ai_flamethrower',
    'neon_annihilator': 'annihilator',
    'third_degree': 'thirddegree',
    'homewrecker': 'sledgehammer',
    'sharpened_volcano_fragment': 'lava_axe',
    'postal_pummeler': 'mailbox',
    # Heavy weapons
    'huo_long_heater': 'long_heatmaker',
    'fists': 'gloves',
    'gru': 'gloves_running_urgently',
    'fists_of_steel': 'steel_fists',
    # Engineer weapons
    'gas_passer': 'gas_blast',
    # Medic weapons
    'vita_saw': 'battleneedle',
    'overdose': 'proto_syringe',
    # Sniper weapons
    'hitman_heatmaker': 'pro_rifle',
    'cleaners_carbine': 'pro_smg',
    'kukri': 'club',
    'bushwacka': 'tribalkukri',
    # Spy weapons
    'big_kill': 'samrevolver',
    'l_etranger': 'letranger',
    'your_eternal_reward': 'eternal_reward',
    'conniver_kunai': 'kunai',
    # Multi-class
    'half_zatoichi': 'demokatana',
    'conscientious_objector': 'nonnonviolent_protest',
    # Taunts
    'taunt_guitar_kill': 'taunt_guitar_kill',
    # Other
    'backscatter': 'back_scatter',
    'nessie_club': 'nessieclub',
    'horseless_headless_horsemann': 'headtaker',
    'sentry_buster': 'ullapool_caber',
    'holy_mackerel': 'holymackerel',
    'pda_engineer': 'saw_kill',
    'tf_projectile_arrow': 'huntsman',
    'cleaver': 'guillotine',
}

# Aliases (same icon, different log names)
WEAPON_ALIASES = {
    'holymackerel': 'holy_mackerel',
    'force-a-nature': 'force_a_nature',
    'lugermorph': 'maxgun',
    'shotgun_soldier': 'shotgun_primary',
    'shotgun_hwg': 'shotgun_primary',
    'shotgun_pyro': 'shotgun_primary',
    'pistol_scout': 'pistol',
    'pistol_engineer': 'pistol',
    'awper_hand': 'sniperrifle',
    'compound_bow': 'huntsman',
}


class KilliconDefinition:
    """Represents a killicon definition from mod_textures.txt"""

    def __init__(self, name: str, sprite: str, x: int, y: int, width: int, height: int):
        self.name = name
        self.sprite = sprite  # 'd_images', 'd_images_v2', or 'd_images_v3'
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def __repr__(self):
        return f"KilliconDefinition({self.name}, {self.sprite}, {self.x}, {self.y}, {self.width}x{self.height})"


def parse_mod_textures(vpk_path: Path) -> Dict[str, KilliconDefinition]:
    """Parse scripts/mod_textures.txt from tf2_misc_dir.vpk"""
    print(f"Opening misc VPK: {vpk_path}")
    pak = vpk.open(str(vpk_path))

    # Read mod_textures.txt
    try:
        entry = pak['scripts/mod_textures.txt']
        content = entry.read().decode('utf-8', errors='ignore')
    except KeyError:
        print("ERROR: Could not find scripts/mod_textures.txt in VPK")
        sys.exit(1)

    # Parse the VDF-like format
    definitions = {}
    lines = content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Look for quoted weapon name
        if line.startswith('"') and not line.startswith('"/'):
            # Extract weapon name
            match = re.match(r'"([^"]+)"', line)
            if match:
                weapon_name = match.group(1)

                # Look for opening brace
                i += 1
                while i < len(lines) and '{' not in lines[i]:
                    i += 1

                # Parse properties
                props = {}
                i += 1
                while i < len(lines):
                    prop_line = lines[i].strip()
                    if '}' in prop_line:
                        break

                    # Parse "key" "value" format
                    prop_match = re.match(r'"([^"]+)"\s+"([^"]+)"', prop_line)
                    if prop_match:
                        key, value = prop_match.groups()
                        props[key.lower()] = value

                    i += 1

                # Check if this is a killicon (has dfile pointing to HUD/d_images*)
                if 'dfile' in props:
                    dfile = props['dfile']
                    if dfile.startswith('HUD/d_images'):
                        # Extract sprite name
                        sprite = dfile.replace('HUD/', '').lower()

                        # Extract coordinates
                        try:
                            x = int(props.get('x', 0))
                            y = int(props.get('y', 0))
                            width = int(props.get('width', 32))
                            height = int(props.get('height', 32))

                            definitions[weapon_name] = KilliconDefinition(
                                weapon_name, sprite, x, y, width, height
                            )
                        except (ValueError, KeyError) as e:
                            print(f"Warning: Could not parse coordinates for {weapon_name}: {e}")

        i += 1

    print(f"Parsed {len(definitions)} killicon definitions from mod_textures.txt")
    return definitions


def extract_sprite_sheets(vpk_path: Path) -> Dict[str, Image.Image]:
    """Extract d_images*.vtf sprite sheets from tf2_textures_dir.vpk"""
    print(f"Opening textures VPK: {vpk_path}")
    pak = vpk.open(str(vpk_path))

    sprites = {}
    sprite_files = {
        'd_images': 'materials/hud/d_images.vtf',
        'd_images_v2': 'materials/hud/d_images_v2.vtf',
        'd_images_v3': 'materials/hud/d_images_v3.vtf',
    }

    for sprite_name, vtf_path in sprite_files.items():
        try:
            print(f"Extracting {vtf_path}...")
            entry = pak[vtf_path]
            vtf_data = entry.read()

            # Convert VTF to PIL Image
            f = io.BytesIO(vtf_data)
            vtf = VTF.read(f)
            frame = vtf.get()
            image = frame.to_PIL()

            sprites[sprite_name] = image
            print(f"  Loaded {sprite_name}: {image.size}")
        except KeyError:
            print(f"Warning: Could not find {vtf_path} in VPK")
        except Exception as e:
            print(f"Error extracting {vtf_path}: {e}")

    return sprites


def parse_community_mod_textures(community_dir: Path) -> Dict[str, KilliconDefinition]:
    """
    Parse scripts/mod_textures.txt from community mod.

    The community mod uses paths like "vgui\\logos\\improvedkillicons\\d"
    which we'll map to sprite names.
    """
    mod_textures_path = community_dir / 'scripts' / 'mod_textures.txt'

    if not mod_textures_path.exists():
        return {}

    print(f"Parsing community mod_textures.txt...")

    with open(mod_textures_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    definitions = {}
    lines = content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Look for quoted weapon name (skip comments)
        if line.startswith('"') and not line.startswith('"/') and not line.startswith('//'):
            # Extract weapon name
            match = re.match(r'"([^"]+)"', line)
            if match:
                weapon_name = match.group(1)

                # Look for opening brace
                i += 1
                while i < len(lines) and '{' not in lines[i]:
                    i += 1

                # Parse properties
                props = {}
                i += 1
                while i < len(lines):
                    prop_line = lines[i].strip()
                    if '}' in prop_line:
                        break

                    # Parse "key" "value" format
                    prop_match = re.match(r'"([^"]+)"\s+"([^"]+)"', prop_line)
                    if prop_match:
                        key, value = prop_match.groups()
                        props[key.lower()] = value

                    i += 1

                # Check if this uses community sprites (improvedkillicons path)
                if 'dfile' in props:
                    dfile = props['dfile']
                    if 'improvedkillicons' in dfile.lower():
                        # Extract sprite name from path like "vgui\logos\improvedkillicons\d"
                        # Map to our internal naming: d -> community_d, d2 -> community_d2, etc.
                        parts = dfile.replace('\\', '/').split('/')
                        sprite_file = parts[-1]  # e.g., "d", "d2", "d3"
                        sprite_name = f'community_{sprite_file}'

                        # Extract coordinates
                        try:
                            x = int(props.get('x', 0))
                            y = int(props.get('y', 0))
                            width = int(props.get('width', 32))
                            height = int(props.get('height', 32))

                            definitions[weapon_name] = KilliconDefinition(
                                weapon_name, sprite_name, x, y, width, height
                            )
                        except (ValueError, KeyError) as e:
                            pass

        i += 1

    print(f"  Found {len(definitions)} community icon definitions")
    return definitions


def load_community_sprites(community_dir: Path) -> Dict[str, Image.Image]:
    """
    Load community mod sprite sheets from ./community/ directory.

    The community mod "Consistent & Missing Kill Icons 2025" by lennyfaic
    provides sprites for weapons not included in TF2's official VPK files.
    Download from: https://gamebanana.com/mods/591386

    Expected structure:
    community/
    ├── materials/vgui/logos/improvedkillicons/
    │   ├── d.vtf, d2.vtf, d3.vtf
    └── scripts/mod_textures.txt
    """
    vtf_dir = community_dir / 'materials' / 'vgui' / 'logos' / 'improvedkillicons'

    if not vtf_dir.exists():
        print("No community sprites found (./community/materials/...)")
        print("Some weapons (telefrag, default, etc.) will be missing icons.")
        print("See README.md for how to get community sprites.")
        return {}

    print(f"Loading community sprites from {vtf_dir}...")

    sprites = {}

    # Load VTF sprite sheets
    for vtf_file in vtf_dir.glob('*.vtf'):
        # Skip inverted versions (dneg*)
        if vtf_file.stem.startswith('dneg'):
            continue

        try:
            # Read VTF and convert to PIL Image
            vtf_data = vtf_file.read_bytes()
            f = io.BytesIO(vtf_data)
            vtf = VTF.read(f)
            frame = vtf.get()
            image = frame.to_PIL()

            sprite_name = f'community_{vtf_file.stem}'
            sprites[sprite_name] = image
            print(f"  Loaded {sprite_name} from {vtf_file.name}: {image.size}")
        except Exception as e:
            print(f"Error loading {vtf_file.name}: {e}")

    return sprites


def find_weapon_icon(weapon_name: str, definitions: Dict[str, KilliconDefinition]) -> Optional[KilliconDefinition]:
    """
    Find the killicon definition for a weapon using fallback logic:
    1. Try exact match
    2. Try with common suffixes (_kill, death)
    3. Try partial match (e.g., pickaxe matches unique_pickaxe)
    4. Check aliases
    """
    # Apply known mappings first
    mapped_name = WEAPON_MAPPINGS.get(weapon_name, weapon_name)

    # 1. Exact match
    if mapped_name in definitions:
        return definitions[mapped_name]

    # 2. Try common suffixes
    for suffix in ['_kill', 'death']:
        candidate = mapped_name + suffix
        if candidate in definitions:
            return definitions[candidate]

    # 3. Partial match - look for weapon name as substring
    for def_name, definition in definitions.items():
        if mapped_name in def_name or def_name in mapped_name:
            return definition

    # 4. Check if this weapon is an alias
    if weapon_name in WEAPON_ALIASES:
        canonical = WEAPON_ALIASES[weapon_name]
        return find_weapon_icon(canonical, definitions)

    return None




def pack_sprites(icons: Dict[str, Tuple[Image.Image, int, int]], aliases: Dict[str, str]) -> Tuple[Image.Image, Dict[str, Tuple[int, int, int, int]]]:
    """
    Pack all icons into a single sprite sheet using simple grid layout

    Args:
        icons: Dict mapping weapon_name -> (image, original_width, original_height)
        aliases: Dict mapping alias_name -> canonical_name for weapons that share icons

    Returns:
        (sprite_sheet, positions) where positions maps weapon_name -> (x, y, width, height)
    """
    if not icons:
        # Create empty 1x1 sprite
        return Image.new('RGBA', (1, 1), (0, 0, 0, 0)), {}

    # Sort icons by height (descending) for better packing
    sorted_icons = sorted(icons.items(), key=lambda x: x[1][0].height, reverse=True)

    # Simple grid packing: pack left to right, top to bottom
    # Target width: ~512px (reasonable for web)
    target_width = 512

    current_x = 0
    current_y = 0
    row_height = 0
    max_width = 0

    positions = {}

    # First pass: calculate positions
    for weapon_name, (img, orig_w, orig_h) in sorted_icons:
        if current_x + img.width > target_width and current_x > 0:
            # Move to next row
            current_x = 0
            current_y += row_height
            row_height = 0

        positions[weapon_name] = (current_x, current_y, img.width, img.height)

        current_x += img.width
        row_height = max(row_height, img.height)
        max_width = max(max_width, current_x)

    # Calculate final sprite dimensions
    final_height = current_y + row_height
    final_width = max_width

    print(f"Sprite sheet size: {final_width}x{final_height}")

    # Create sprite sheet
    sprite = Image.new('RGBA', (final_width, final_height), (0, 0, 0, 0))

    # Paste icons
    for weapon_name, (x, y, w, h) in positions.items():
        img = icons[weapon_name][0]
        sprite.paste(img, (x, y))

    # Add alias positions (same position as canonical weapon)
    for alias, canonical in aliases.items():
        if canonical in positions:
            positions[alias] = positions[canonical]

    return sprite, positions


def generate_css(positions: Dict[str, Tuple[int, int, int, int]], output_path: Path):
    """Generate CSS file with killicon classes"""

    css_lines = [
        "/* TF2 Killicons - Auto-generated */",
        "",
        ".killicon {",
        "  display: inline-block;",
        "  background-image: url('killicons.webp');",
        "  background-repeat: no-repeat;",
        "  vertical-align: middle;",
        "}",
        "",
    ]

    # Collect all weapon names (including reverse mappings)
    all_weapons = set(positions.keys())

    # Add reverse mappings: for each mapping, create a class for the original name
    # that points to the mapped name's position
    reverse_mappings = {}
    for original, mapped in WEAPON_MAPPINGS.items():
        if mapped in positions:
            reverse_mappings[original] = mapped
            all_weapons.add(original)

    # Sort by weapon name for readability
    for weapon_name in sorted(all_weapons):
        # Check if this is a reverse mapping
        if weapon_name in reverse_mappings:
            # Use the position of the mapped weapon
            mapped_name = reverse_mappings[weapon_name]
            x, y, width, height = positions[mapped_name]
        elif weapon_name in positions:
            x, y, width, height = positions[weapon_name]
        else:
            continue

        css_lines.extend([
            f".killicon-{weapon_name} {{",
            f"  width: {width}px;",
            f"  height: {height}px;",
            f"  background-position: -{x}px -{y}px;",
            "}",
            "",
        ])

    output_path.write_text('\n'.join(css_lines))
    print(f"Generated CSS: {output_path}")


def main():
    print("=" * 60)
    print("TF2 Killicons Generator")
    print("=" * 60)
    print()

    # Check VPK files exist
    vpk_dir = Path('vpk')
    misc_vpk = vpk_dir / 'tf2_misc_dir.vpk'
    textures_vpk = vpk_dir / 'tf2_textures_dir.vpk'

    if not misc_vpk.exists():
        print(f"ERROR: {misc_vpk} not found!")
        print("Please copy tf2_misc_dir.vpk to the vpk/ directory")
        sys.exit(1)

    if not textures_vpk.exists():
        print(f"ERROR: {textures_vpk} not found!")
        print("Please copy tf2_textures_dir.vpk (and all tf2_textures_*.vpk files) to the vpk/ directory")
        sys.exit(1)

    # Parse mod_textures.txt
    print("\n[1/5] Parsing mod_textures.txt...")
    definitions = parse_mod_textures(misc_vpk)

    # Extract sprite sheets
    print("\n[2/5] Extracting sprite sheets...")
    sprites = extract_sprite_sheets(textures_vpk)

    if not sprites:
        print("ERROR: No sprite sheets found!")
        sys.exit(1)

    # Load community sprites and definitions
    print("\n[2.5/5] Loading community mod...")
    community_dir = Path('community')
    community_sprites = load_community_sprites(community_dir)
    community_definitions = parse_community_mod_textures(community_dir)

    # Merge community sprites and definitions into main collections
    sprites.update(community_sprites)
    definitions.update(community_definitions)

    if community_sprites:
        print(f"  Loaded {len(community_sprites)} community sprite sheets")
        print(f"  Added {len(community_definitions)} community weapon definitions")
    else:
        print("\nWARNING: No community mod found!")
        print("Only 318/324 weapons will be available.")
        print("See README.md for how to get community sprites.")

    # Use all weapon definitions found in VPK and community mod
    print(f"\n[3/5] Processing {len(definitions)} weapon definitions...")
    weapons = list(definitions.keys())

    # Extract icons for each weapon
    print("\n[4/5] Extracting icons...")
    icons = {}
    missing = []

    for weapon_name in weapons:
        definition = find_weapon_icon(weapon_name, definitions)

        if not definition:
            missing.append(weapon_name)
            continue

        # Get the sprite sheet
        if definition.sprite not in sprites:
            print(f"Warning: Sprite sheet '{definition.sprite}' not found for {weapon_name}")
            continue

        sprite = sprites[definition.sprite]

        # Extract icon region
        try:
            icon = sprite.crop((
                definition.x,
                definition.y,
                definition.x + definition.width,
                definition.y + definition.height
            ))

            icons[weapon_name] = (icon, definition.width, definition.height)
        except Exception as e:
            print(f"Error extracting {weapon_name}: {e}")

    print(f"Extracted {len(icons)} icons")

    if missing:
        print(f"\nWarning: {len(missing)} weapons have no icons:")
        for weapon in sorted(missing)[:20]:  # Show first 20
            print(f"  - {weapon}")
        if len(missing) > 20:
            print(f"  ... and {len(missing) - 20} more")

    # Pack sprites
    print("\n[5/5] Generating sprite sheet and CSS...")
    sprite_sheet, positions = pack_sprites(icons, WEAPON_ALIASES)

    # Save outputs
    dist_dir = Path('dist')
    dist_dir.mkdir(exist_ok=True)

    output_webp = dist_dir / 'killicons.webp'
    output_css = dist_dir / 'killicons.css'

    # Save as WebP
    sprite_sheet.save(output_webp, 'WEBP', quality=90, method=6)
    file_size = output_webp.stat().st_size / 1024
    print(f"Generated sprite: {output_webp} ({file_size:.1f} KB)")

    # Generate CSS
    generate_css(positions, output_css)

    print()
    print("=" * 60)
    print("Done!")
    print(f"  {len(icons)}/{len(weapons)} weapons processed")
    print(f"  Sprite: {output_webp}")
    print(f"  CSS: {output_css}")
    print("=" * 60)


if __name__ == "__main__":
    main()
