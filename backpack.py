#!/usr/bin/env python3
"""Writes every TF2 backpack picture as a WebP plus items.json (defindex -> picture name)."""

import argparse
import io
import json
import sys
from pathlib import Path

import vpk
from PIL import Image
from srctools import Keyvalues
from srctools.vtf import VTF

PREFIX = "materials/backpack/"
HEIGHT = 64


def image_name(path: str) -> str:
    return path.rsplit("/", 1)[-1]


def parse_items_game(text: str) -> dict[int, str]:
    root = Keyvalues.parse(text).find_block("items_game")
    prefabs = {kv.real_name: kv for kv in root.find_block("prefabs")}

    def resolve(kv: Keyvalues, seen: frozenset = frozenset()) -> str | None:
        own = kv.find_key("image_inventory", "").value
        if own:
            return own
        names = kv.find_key("prefab", "").value.split()
        for name in reversed(names):
            if name in prefabs and name not in seen:
                found = resolve(prefabs[name], seen | {name})
                if found:
                    return found
        return None

    result = {}
    for kv in root.find_block("items"):
        if not kv.real_name.isdigit():
            continue
        path = resolve(kv)
        if path:
            result[int(kv.real_name)] = path
    return result


def render(data: bytes) -> Image.Image:
    img = VTF.read(io.BytesIO(data)).get().to_PIL().convert("RGBA")
    box = img.getchannel("A").getbbox()
    if box:
        img = img.crop(box)
    width = max(1, round(img.width * HEIGHT / img.height))
    return img.resize((width, HEIGHT), Image.LANCZOS)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--items-game", required=True, type=Path)
    ap.add_argument("--out", default=Path("dist/backpack"), type=Path)
    ap.add_argument("--vpk", default=Path("vpk/tf2_textures_dir.vpk"), type=Path)
    args = ap.parse_args()

    pak = vpk.open(str(args.vpk))
    paths = sorted(p for p in pak if p.startswith(PREFIX) and p.endswith(".vtf")
                   and not p[:-4].endswith("_large"))
    args.out.mkdir(parents=True, exist_ok=True)

    written, failed = set(), 0
    for i, path in enumerate(paths, 1):
        name = image_name(path[:-4])
        try:
            render(pak[path].read()).save(args.out / f"{name}.webp", "WEBP", quality=80)
            written.add(name)
        except Exception as e:
            failed += 1
            print(f"skip {path}: {e}", file=sys.stderr)
        if i % 250 == 0 or i == len(paths):
            print(f"{i}/{len(paths)}", flush=True)

    items = parse_items_game(args.items_game.read_text(encoding="utf-8"))
    mapping = {str(d): image_name(p) for d, p in sorted(items.items())
               if image_name(p) in written}
    (args.out / "items.json").write_text(json.dumps(mapping, indent=0))
    print(f"{len(written)} images, {failed} failed, {len(mapping)} items mapped")


if __name__ == "__main__":
    main()
