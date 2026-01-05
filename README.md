# TF2 Killicons Sprite Generator

Generates an optimized sprite sheet and CSS file from TF2's VPK files for use in web applications displaying TF2 log data.

## Features

- Extracts 297 weapons from TF2's official VPK files
- Optional community mod support for 241+ additional weapons
- Generates optimized WebP sprite sheet (~287KB)
- Auto-generates CSS with 380+ weapon classes
- Docker support for easy deployment
- Self-contained - no external dependencies required

## Quick Start

### Prerequisites

You need:
1. **TF2 VPK files** - Copy from your Team Fortress 2 installation to `./vpk/`
2. **(Optional) Community mod** - For 100% weapon coverage, download and extract to `./community/`

See [Setup](#setup) section below for detailed instructions.

### Option 1: Docker (Recommended)

No Python installation needed - just Docker and your TF2 VPK files.

```bash
# 1. Copy VPK files to ./vpk/ (see Setup section)

# 2. (Optional) Copy community mod to ./community/ for full coverage

# 3. Build the image
docker build -t tf2-killicons .

# 4. Run the generator (single line - no backslashes needed)
docker run --rm -v "$(pwd)/vpk:/app/vpk:ro" -v "$(pwd)/community:/app/community:ro" -v "$(pwd)/dist:/app/dist" tf2-killicons
```

Output files will be in `./dist/killicons.webp` and `./dist/killicons.css`

### Option 2: Python + uv

```bash
# 1. Copy VPK files to ./vpk/ (see Setup section)

# 2. (Optional) Copy community mod to ./community/ for full coverage

# 3. Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 4. Run the generator
uv run generate.py
```

## Setup

### 1. Copy VPK Files

You need to copy VPK files from your TF2 installation to `./vpk/`:

**Linux:**
```bash
cp ~/.steam/steam/steamapps/common/Team\ Fortress\ 2/tf/tf2_misc_dir.vpk ./vpk/
cp ~/.steam/steam/steamapps/common/Team\ Fortress\ 2/tf/tf2_misc_*.vpk ./vpk/
cp ~/.steam/steam/steamapps/common/Team\ Fortress\ 2/tf/tf2_textures_dir.vpk ./vpk/
cp ~/.steam/steam/steamapps/common/Team\ Fortress\ 2/tf/tf2_textures_*.vpk ./vpk/
```

**Windows:**
Copy from `C:\Program Files (x86)\Steam\steamapps\common\Team Fortress 2\tf\`

### 2. (Optional) Add Community Mod

See [Community Sprites](#community-sprites-recommended-for-full-coverage) section below.

## Output Files

After running the generator, you'll find:

- **`dist/killicons.webp`** - Optimized sprite sheet (WebP format, ~287KB with community mod)
- **`dist/killicons.css`** - CSS with 380+ weapon classes
- **`dist/killicons_preview.png`** - Visual preview of all icons (optional)

## Usage in HTML

```html
<link rel="stylesheet" href="killicons.css">

<!-- Use weapon names from TF2 server log lines -->
<span class="killicon killicon-scattergun"></span>
<span class="killicon killicon-tf_projectile_rocket"></span>
<span class="killicon killicon-world"></span>
<span class="killicon killicon-telefrag"></span>
```

The generator creates CSS classes for weapon names exactly as they appear in TF2 server logs, so you can use log line weapon names directly as class names.

## Community Sprites (Recommended for Full Coverage)

**TF2's official VPK files contain 297 weapon icons.** For additional coverage including community weapons, custom icons, and missing vanilla weapons, use the community mod:

**[Consistent & Missing Kill Icons 2025](https://gamebanana.com/mods/591386)** from GameBanana

### What You'll Get

**Without community mod** (VPKs only):
- 297 weapon definitions from TF2's official files
- ~270 unique icons extracted
- Missing some weapons like `telefrag`, `entity_medigun_shield`, etc.

**With community mod**:
- 538 total weapon definitions (297 from TF2 + 241 from community mod)
- 312 unique icons extracted
- 380+ CSS classes (includes aliases for common weapon name variations)
- Full coverage including:
  - `telefrag`
  - `entity_medigun_shield` (MvM)
  - `tf_projectile_grapplinghook` (Mannpower)
  - `tf_projectile_mechanicalarmor` (MvM)
  - Many improved/enhanced versions of vanilla icons

### Installation

1. **Download** the mod from [GameBanana](https://gamebanana.com/mods/591386)
2. **Extract** the downloaded archive
3. **Copy** the entire extracted folder contents to `./community/`:
   ```bash
   # Example: if you extracted to ~/Downloads/improvedkillicons/
   cp -r ~/Downloads/improvedkillicons/* ./community/
   ```

   Expected structure:
   ```
   community/
   ├── materials/vgui/logos/improvedkillicons/
   │   ├── d.vtf, d2.vtf, d3.vtf (sprite sheets)
   │   └── d.vmt, d2.vmt, d3.vmt (material files)
   └── scripts/
       └── mod_textures.txt (icon coordinates)
   ```

4. **Re-run** the generator - it will automatically detect and parse the community mod

The generator automatically merges community icons with TF2's official icons. No configuration needed!

## Additional Commands

### Generate Visual Preview

Create a PNG showing all weapon icons with their names:

```bash
# With Docker
docker run --rm -v "$(pwd)/dist:/app/dist" tf2-killicons python3 generate_preview.py --all

# Without Docker
uv run generate_preview.py --all
```

Output: `dist/killicons_preview.png` (useful for visual verification)

### Verify Weapon Coverage

Check which weapons from your list are included:

```bash
# Create a file with weapon names (one per line)
echo -e "scattergun\nrocketlauncher\ntelefrag" > weapons.txt

# Generate preview for just those weapons
uv run generate_preview.py
```

## Technical Details

### Sprite Sheet Format

- **Format**: WebP (optimized for web)
- **Size**: ~287KB (with community mod), ~230KB (VPKs only)
- **Layout**: Efficient grid packing (512px width)
- **Source**: TF2 VPK files + optional community mod VTF files

### CSS Classes

The generator creates two types of CSS classes:

1. **Direct definitions** - Weapons with icons in the source files
2. **Aliases** - Common weapon name variations that map to the same icon

Examples:
- `killicon-grenadelauncher` → maps to `tf_projectile_pipe` icon
- `killicon-rocketlauncher` → maps to `tf_projectile_rocket` icon
- `killicon-world` → maps to `skull` icon

All 380+ classes are fully compatible with TF2 server log weapon names.

## Troubleshooting

### "No VPK files found"

Make sure you've copied all required VPK files to `./vpk/`:
- `tf2_misc_dir.vpk` and all `tf2_misc_*.vpk` files
- `tf2_textures_dir.vpk` and all `tf2_textures_*.vpk` files

### "Missing X weapons"

This is normal if you haven't installed the community mod. The 6 missing weapons are only available in the community mod.

### Docker volume mount issues

If you're on Windows using PowerShell, use:
```powershell
docker run --rm -v "${PWD}/vpk:/app/vpk:ro" -v "${PWD}/dist:/app/dist" tf2-killicons
```

### Permission issues with Docker

If the generated files have wrong permissions, you can change ownership:
```bash
sudo chown -R $USER:$USER dist/
```

