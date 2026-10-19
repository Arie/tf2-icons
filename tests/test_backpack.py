from backpack import image_name, parse_items_game

SAMPLE = '''
"items_game"
{
    "prefabs"
    {
        "base_medigun"
        {
            "image_inventory" "backpack/weapons/c_models/c_medigun/c_medigun"
        }
        "weapon_medigun"
        {
            "prefab" "base_medigun valve"
        }
        "valve"
        {
            "name" "x"
        }
    }
    "items"
    {
        "default"
        {
            "name" "default"
        }
        "29"
        {
            "name" "Medi Gun"
            "prefab" "weapon_medigun"
        }
        "35"
        {
            "name" "Kritzkrieg"
            "prefab" "weapon_medigun"
            "image_inventory" "backpack/weapons/c_models/c_overhealer/c_overhealer"
        }
        "5"
        {
            "name" "No image"
        }
    }
}
'''


def test_prefab_inheritance():
    items = parse_items_game(SAMPLE)
    assert items[29] == "backpack/weapons/c_models/c_medigun/c_medigun"
    assert items[35] == "backpack/weapons/c_models/c_overhealer/c_overhealer"
    assert 5 not in items
    assert "default" not in items


def test_image_name():
    assert image_name("backpack/weapons/c_models/c_overhealer/c_overhealer") == "c_overhealer"
