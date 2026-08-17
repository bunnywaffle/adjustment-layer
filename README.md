# Adjustment Layer & Layer Effects for GIMP 3

A high-performance Python plug-in that brings **Photoshop-style Adjustment Layers** and **Non-Destructive Layer Effects** to GIMP 3.0, 3.2, and newer using GIMP's Non-Destructive Editing (NDE) engine and GEGL.

---

## Key Features

- 🪄 **Selection-Aware Masking**: If an active selection is present when creating an adjustment layer, it is automatically converted into the layer mask—applying adjustments strictly to the selected area.
- 🎨 **19 Professional Adjustment Layers**: Complete tonal, color, blur, and creative adjustments powered by high-precision 32-bit floating point GEGL operations.
- ⚡ **Instant Zero-Friction Creation**: No redundant pop-up dialogs. Layers and effects are created instantly on the canvas with full native live controls in GIMP's Layers dock.
- 🔄 **Fully Non-Destructive (NDE)**: Adjustments and layer effects remain live! You can edit properties at any time directly in the Layers dock / filters list.
- 🎭 **Dedicated Layer Effects**: Apply non-destructive Stroke / Outline, Drop Shadow, Long Shadow, Bevel & Emboss, Inner Glow, and Multi-Effect Layer Styles directly to any layer or group.
- 🛡️ **Clean Undo / Redo**: Every action is encapsulated in a single undo group for clean, reliable Ctrl+Z undo/redo.

---

## Available Adjustment Layers

Access via **Layer > Adjustment Layer**, **Image > Adjustment Layer**, or **Colors > Adjustment Layer**:

| Adjustment Layer | GEGL Operation | Description & Key Parameters |
|---|---|---|
| **Saturation** | `gegl:saturation` | Scale color saturation factor (0.0 to 5.0). |
| **Bloom** | `gegl:bloom` | Glow radius, strength, highlight threshold, softness, and exposure limit. |
| **Invert** | `gegl:invert-gamma` | Perceptually uniform gamma-corrected color inversion. |
| **Vibrance** | `gegl:vibrance` | Boosts muted colors intelligently without oversaturating skin tones. |
| **Channel Mixer** | `gegl:mono-mixer` | Custom Red, Green, Blue channel weights with luminosity preservation. |
| **Color Rotate** | `gegl:color-rotate` | Shift and remap hue ranges with degree-based angle controls. |
| **Exposure** | `gegl:exposure` | Photographic exposure adjustment in stops and black-level offset. |
| **Curves (Contrast Curve)** | `gegl:contrast-curve` | Tonal contrast curves with sampling point control. |
| **Brightness-Contrast** | `gegl:brightness-contrast` | Standard brightness offset and contrast multiplier. |
| **Levels** | `gegl:levels` | Input/Output black point and white point clipping controls. |
| **Hue-Saturation (Hue-Chroma)** | `gegl:hue-chroma` | 360° Hue shift, Chroma boost/reduction, and Lightness adjustment. |
| **Color Temperature** | `gegl:color-temperature` | Kelvin temperature adjustments (warm/cool white balance correction). |
| **Sepia** | `gegl:sepia` | Classic sepia photographic toning with scale factor. |
| **Black & White (Color to Gray)** | `gegl:c2g` | Advanced local-contrast grayscale conversion with iterations and sampling. |
| **Threshold** | `gegl:threshold` | High-contrast binary black/white cutoff threshold. |
| **Gaussian Blur** | `gegl:gaussian-blur` | Independent horizontal and vertical standard deviation blur radii. |
| **High Pass** | `gegl:high-pass` | High-frequency detail extraction for frequency separation & sharpening. |
| **Unsharp Mask** | `gegl:unsharp-mask` | Radius, amount/scale, and threshold sharpening controls. |
| **Vignette** | `gegl:vignette` | Radial exposure falloff with radius, softness, and gamma curvature. |

---

## Available Layer Effects

Access via **Layer > Layer Effects** or **Filters > Layer Effects**:

| Layer Effect | GEGL Operation | Description & Parameters |
|---|---|---|
| **Stroke / Outline** | `gegl:dropshadow` | Clean outer outline/stroke with thickness, color, and opacity. |
| **Drop Shadow** | `gegl:dropshadow` | X/Y pixel offsets, blur radius, opacity, and grow/spread radius. |
| **Long Shadow** | `gegl:long-shadow` | Direction angle, projection length, and midpoint falloff. |
| **Bevel & Emboss** | `gegl:bevel` | Bevel radius, light elevation, depth percentage, and azimuth angle. |
| **Inner Glow** | `gegl:inner-glow` | Inner glow radius, spread grow-radius, and opacity. |
| **Layer Styles** | `gegl:styles` | Multi-style layer effects (stroke, shadow, bevel, glow, overlay). |

---

## Installation

1. Copy `adjustment-layer.py` into your GIMP plug-ins folder inside a directory named `adjustment-layer`:

| Operating System | Plug-in Directory Path |
|---|---|
| **Windows** | `%APPDATA%\GIMP\3.2\plug-ins\adjustment-layer\` (or `3.0`) |
| **Linux** | `~/.config/GIMP/3.2/plug-ins/adjustment-layer/` (or `3.0`) |
| **macOS** | `~/Library/Application Support/GIMP/3.2/plug-ins/adjustment-layer/` (or `3.0`) |

2. **Linux / macOS**: Ensure the file is executable:
   ```bash
   chmod +x adjustment-layer.py
   ```

3. Restart GIMP.

---

## Requirements

- GIMP 3.0, 3.2, or newer
- Python 3 support enabled in GIMP

---

## License

[GNU General Public License v3.0](LICENSE)
