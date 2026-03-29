# Adjustment Layer for GIMP 3

A Python plug-in that adds **Photoshop-style Adjustment Layers** to GIMP 3.0 / 3.2 using the new Non-Destructive Editing (NDE) features.

## How It Works

Each adjustment creates a **Layer Group** set to **Pass Through** blend mode with a GEGL/GIMP filter applied non-destructively. A white layer mask is added so you can paint with black to hide the adjustment from specific areas — exactly like Photoshop's adjustment layers.

## Available Adjustments

| Adjustment | Operation |
|---|---|
| Hue-Saturation | `gimp:hue-saturation` |
| Color Balance | `gimp:color-balance` |
| Brightness-Contrast | `gimp:brightness-contrast` |
| Levels | `gimp:levels` |
| Curves | `gimp:curves` |
| Exposure | `gegl:exposure` |
| Colorize | `gimp:colorize` |
| Channel Mixer | `gegl:channel-mixer` |
| Shadows-Highlights | `gegl:shadows-highlights` |
| Color Exchange | `gegl:color-exchange` |
| Vibrance | `gegl:vibrance` |
| Invert | `gegl:invert-gamma` |
| Gaussian Blur | `gegl:gaussian-blur` |
| Bloom | `gegl:bloom` |
| Lens Flare | `gegl:lens-flare` |
| Vignette | `gegl:vignette` |

## Features

- **Non-destructive** — edit filter properties anytime by clicking the filter in the Layers panel
- **Selection-aware masks** — if you have an active selection, it becomes the layer mask
- **Undo-safe** — the entire operation is wrapped in a single undo group

## Installation

1. Download `adjustment-layer.py`
2. Place it inside a folder named `adjustment-layer` in your GIMP plug-ins directory:

| OS | Path |
|---|---|
| **Windows** | `%APPDATA%\GIMP\3.0\plug-ins\adjustment-layer\` |
| **Linux** | `~/.config/GIMP/3.0/plug-ins/adjustment-layer/` |
| **macOS** | `~/Library/Application Support/GIMP/3.0/plug-ins/adjustment-layer/` |

3. **Linux/macOS:** Make the file executable:
   ```bash
   chmod +x adjustment-layer.py
   ```
4. Restart GIMP

The menu appears at **Image > Adjustment Layer**.

## Usage

1. Open an image in GIMP
2. Select a layer
3. Go to **Image > Adjustment Layer** and choose an adjustment
4. A properties dialog opens — adjust the values and click OK
5. A new pass-through layer group appears above your selected layer
6. Paint on the white mask with black to hide the adjustment where needed

## Requirements

- GIMP 3.0 or newer (including 3.2)
- Python 3 support enabled in GIMP

## License

[GPLv3](LICENSE)
