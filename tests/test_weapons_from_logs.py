from pathlib import Path

import pytest

from generate import find_weapon_icon, parse_community_mod_textures, parse_mod_textures

ROOT = Path(__file__).parent.parent
MISC_VPK = ROOT / 'vpk' / 'tf2_misc_dir.vpk'
COMMUNITY_DIR = ROOT / 'community'
COMMUNITY_MOD_TEXTURES = COMMUNITY_DIR / 'scripts' / 'mod_textures.txt'

# Weapon names seen in kill lines of real TF2 server logs. Non-lethal items that
# show up in logs (dispenser, teleporter, buff_item, parachute, tf_weapon_jar,
# tf_weapon_medigun) are deliberately left out.
WEAPONS = (Path(__file__).parent / 'weapons_from_logs.txt').read_text().split()


@pytest.fixture(scope='module')
def definitions():
    if not MISC_VPK.exists() or not COMMUNITY_MOD_TEXTURES.exists():
        pytest.skip('VPK files or community mod not present')
    definitions = parse_mod_textures(MISC_VPK)
    definitions.update(parse_community_mod_textures(COMMUNITY_DIR))
    return definitions


@pytest.mark.parametrize('weapon', WEAPONS)
def test_weapon_from_logs_has_icon(weapon, definitions):
    assert find_weapon_icon(weapon, definitions) is not None
