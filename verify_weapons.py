#!/usr/bin/env python3
"""Verify which weapons from a list have killicon sprites"""

import sys
from pathlib import Path
from generate import (
    parse_mod_textures,
    parse_community_mod_textures,
    WEAPON_MAPPINGS,
    WEAPON_ALIASES,
    find_weapon_icon
)

def main():
    # Parse weapon list from stdin or file
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            weapons = [line.strip() for line in f if line.strip()]
    else:
        weapons = [line.strip() for line in sys.stdin if line.strip()]

    # Load definitions
    vpk_dir = Path('vpk')
    misc_vpk = vpk_dir / 'tf2_misc_dir.vpk'

    if not misc_vpk.exists():
        print("ERROR: VPK files not found!")
        sys.exit(1)

    print("Loading definitions...")
    definitions = parse_mod_textures(misc_vpk)

    # Load community definitions
    community_dir = Path('community')
    community_definitions = parse_community_mod_textures(community_dir)
    definitions.update(community_definitions)

    print(f"Loaded {len(definitions)} weapon definitions\n")

    # Check each weapon
    found = []
    aliases = []
    missing = []

    for weapon in sorted(weapons):
        # Check if it's directly defined
        if weapon in definitions:
            found.append((weapon, weapon, 'direct'))
        # Check if it's mapped
        elif weapon in WEAPON_MAPPINGS:
            mapped = WEAPON_MAPPINGS[weapon]
            if find_weapon_icon(weapon, definitions):
                found.append((weapon, mapped, 'mapped'))
            else:
                missing.append((weapon, f"mapped to '{mapped}' but not found"))
        # Check if it's an alias
        elif weapon in WEAPON_ALIASES:
            canonical = WEAPON_ALIASES[weapon]
            if find_weapon_icon(weapon, definitions):
                aliases.append((weapon, canonical))
            else:
                missing.append((weapon, f"alias of '{canonical}' but not found"))
        # Try to find it with fallback logic
        elif find_weapon_icon(weapon, definitions):
            result = find_weapon_icon(weapon, definitions)
            found.append((weapon, result.name, 'fallback'))
        else:
            missing.append((weapon, 'no icon found'))

    # Print results
    print(f"✓ FOUND: {len(found)}/{len(weapons)} weapons have sprites")
    print(f"→ ALIASES: {len(aliases)} weapons are aliases")
    print(f"✗ MISSING: {len(missing)} weapons have no sprites\n")

    if aliases:
        print("=" * 60)
        print("ALIASES (same icon, different names):")
        print("=" * 60)
        for weapon, canonical in sorted(aliases):
            print(f"  {weapon:40s} → {canonical}")
        print()

    if missing:
        print("=" * 60)
        print("MISSING WEAPONS:")
        print("=" * 60)
        for weapon, reason in sorted(missing):
            print(f"  {weapon:40s} ({reason})")
        print()

    # Print some examples of mapped weapons for context
    if found:
        mapped_examples = [(w, target, typ) for w, target, typ in found if typ == 'mapped'][:10]
        if mapped_examples:
            print("=" * 60)
            print("EXAMPLE MAPPINGS (log name → icon name):")
            print("=" * 60)
            for weapon, target, _ in mapped_examples:
                print(f"  {weapon:40s} → {target}")

if __name__ == '__main__':
    main()
