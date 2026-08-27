#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
Adjustment Layer & Layer Effects Plug-in for GIMP 3.0 / 3.2+
==============================================================================
Provides non-destructive Photoshop-style Adjustment Layers using Pass-Through
Layer Groups and GEGL filters with selection-aware layer masks, as well as
direct Non-Destructive Layer Effects.

When an adjustment layer or layer effect is added, its effect adjustment
dialog opens immediately with live on-canvas controls so the user can tweak
parameters in real-time.

Menu Locations:
- Layer > Adjustment Layer > [Adjustment]
- Image > Adjustment Layer > [Adjustment]
- Colors > Adjustment Layer > [Adjustment]
- Layer > Layer Effects > [Effect]
- Filters > Layer Effects > [Effect]

------------------------------------------------------------------------------
HOW TO ADD NEW ADJUSTMENTS OR EFFECTS IN THE FUTURE:
------------------------------------------------------------------------------
Adding a new adjustment layer or layer effect takes just ONE entry in either
ADJUSTMENTS or LAYER_EFFECTS below:

Example:
   "oilify": {
       "name": "Oilify",
       "op": "gegl:oilify",
       "label": "_Oilify...",
       "args": [
           {"name": "mask-radius", "type": "int", "nick": "Radius", "min": 1, "max": 50, "default": 5},
       ],
   }
==============================================================================
"""

import sys
import gi

gi.require_version("Gimp", "3.0")
gi.require_version("GimpUi", "3.0")
gi.require_version("Gegl", "0.4")
from gi.repository import Gimp, GimpUi, Gegl, GObject, GLib

# Initialize GEGL subsystem
Gegl.init(None)

ADJ_PREFIX = "plug-in-adjustment-layer-"
FX_PREFIX = "plug-in-layer-effect-"

# ============================================================================
# ADJUSTMENT LAYERS REGISTRY
# ============================================================================

ADJUSTMENTS = {
    # --- Color & Tonal Adjustments ---
    "saturation": {
        "label": "_Saturation...",
        "name": "Saturation",
        "op": "gegl:saturation",
        "args": [
            {
                "name": "scale",
                "type": "double",
                "nick": "Scale",
                "blurb": "Saturation scaling factor (1.0 = normal)",
                "min": 0.0,
                "max": 5.0,
                "default": 1.2,
            }
        ],
    },
    "vibrance": {
        "label": "_Vibrance...",
        "name": "Vibrance",
        "op": "gegl:vibrance",
        "args": [
            {
                "name": "vibrance",
                "type": "double",
                "nick": "Vibrance",
                "blurb": "Vibrance adjustment (boosts muted colors)",
                "min": -1.0,
                "max": 1.0,
                "default": 0.25,
            },
            {
                "name": "saturation",
                "type": "double",
                "nick": "Saturation Multiplier",
                "blurb": "Overall saturation multiplier",
                "min": 0.0,
                "max": 2.0,
                "default": 1.0,
            },
        ],
    },
    "exposure": {
        "label": "_Exposure...",
        "name": "Exposure",
        "op": "gegl:exposure",
        "args": [
            {
                "name": "exposure",
                "type": "double",
                "nick": "Exposure (Stops)",
                "blurb": "Relative brightness change in exposure stops",
                "min": -10.0,
                "max": 10.0,
                "default": 0.0,
            },
            {
                "name": "black-level",
                "type": "double",
                "nick": "Black Level",
                "blurb": "Adjust the black level offset",
                "min": -0.1,
                "max": 0.1,
                "default": 0.0,
            },
        ],
    },
    "brightness-contrast": {
        "label": "_Brightness-Contrast...",
        "name": "Brightness-Contrast",
        "op": "gegl:brightness-contrast",
        "args": [
            {
                "name": "brightness",
                "type": "double",
                "nick": "Brightness",
                "blurb": "Amount to increase or decrease brightness",
                "min": -1.0,
                "max": 1.0,
                "default": 0.0,
            },
            {
                "name": "contrast",
                "type": "double",
                "nick": "Contrast",
                "blurb": "Amount to scale contrast (1.0 = unchanged)",
                "min": -1.0,
                "max": 5.0,
                "default": 1.0,
            },
        ],
    },
    "levels": {
        "label": "_Levels...",
        "name": "Levels",
        "op": "gegl:levels",
        "args": [
            {
                "name": "in-low",
                "type": "double",
                "nick": "Input Black Point",
                "blurb": "Input low black level",
                "min": 0.0,
                "max": 1.0,
                "default": 0.0,
            },
            {
                "name": "in-high",
                "type": "double",
                "nick": "Input White Point",
                "blurb": "Input high white level",
                "min": 0.0,
                "max": 1.0,
                "default": 1.0,
            },
            {
                "name": "out-low",
                "type": "double",
                "nick": "Output Black Point",
                "blurb": "Output low black level",
                "min": 0.0,
                "max": 1.0,
                "default": 0.0,
            },
            {
                "name": "out-high",
                "type": "double",
                "nick": "Output White Point",
                "blurb": "Output high white level",
                "min": 0.0,
                "max": 1.0,
                "default": 1.0,
            },
        ],
    },
    "curves": {
        "label": "_Curves (Contrast Curve)...",
        "name": "Curves",
        "op": "gegl:contrast-curve",
        "args": [
            {
                "name": "sampling-points",
                "type": "int",
                "nick": "Sampling Points",
                "blurb": "Number of curve sampling points",
                "min": 0,
                "max": 256,
                "default": 0,
            }
        ],
    },
    "hue-chroma": {
        "label": "Hue-_Saturation (Hue-Chroma)...",
        "name": "Hue-Saturation",
        "op": "gegl:hue-chroma",
        "args": [
            {
                "name": "hue",
                "type": "double",
                "nick": "Hue Shift (°)",
                "blurb": "Hue rotation angle in degrees",
                "min": -180.0,
                "max": 180.0,
                "default": 0.0,
            },
            {
                "name": "chroma",
                "type": "double",
                "nick": "Chroma / Saturation",
                "blurb": "Chroma color saturation adjustment",
                "min": -100.0,
                "max": 100.0,
                "default": 0.0,
            },
            {
                "name": "lightness",
                "type": "double",
                "nick": "Lightness",
                "blurb": "Lightness adjustment",
                "min": -100.0,
                "max": 100.0,
                "default": 0.0,
            },
        ],
    },
    "channel-mixer": {
        "label": "Channel _Mixer...",
        "name": "Channel Mixer",
        "op": "gegl:mono-mixer",
        "args": [
            {
                "name": "preserve-luminosity",
                "type": "boolean",
                "nick": "Preserve Luminosity",
                "blurb": "Preserve overall perceived brightness",
                "default": True,
            },
            {
                "name": "red",
                "type": "double",
                "nick": "Red Weight",
                "blurb": "Red channel contribution",
                "min": -2.0,
                "max": 2.0,
                "default": 0.333,
            },
            {
                "name": "green",
                "type": "double",
                "nick": "Green Weight",
                "blurb": "Green channel contribution",
                "min": -2.0,
                "max": 2.0,
                "default": 0.333,
            },
            {
                "name": "blue",
                "type": "double",
                "nick": "Blue Weight",
                "blurb": "Blue channel contribution",
                "min": -2.0,
                "max": 2.0,
                "default": 0.333,
            },
        ],
    },
    "color-rotate": {
        "label": "Color _Rotate...",
        "name": "Color Rotate",
        "op": "gegl:color-rotate",
        "args": [
            {
                "name": "src-from",
                "type": "double",
                "nick": "Source From (°)",
                "blurb": "Source hue range start angle in degrees",
                "min": 0.0,
                "max": 360.0,
                "default": 0.0,
            },
            {
                "name": "src-to",
                "type": "double",
                "nick": "Source To (°)",
                "blurb": "Source hue range end angle in degrees",
                "min": 0.0,
                "max": 360.0,
                "default": 360.0,
            },
            {
                "name": "dest-from",
                "type": "double",
                "nick": "Destination From (°)",
                "blurb": "Destination hue range start angle in degrees",
                "min": 0.0,
                "max": 360.0,
                "default": 0.0,
            },
            {
                "name": "dest-to",
                "type": "double",
                "nick": "Destination To (°)",
                "blurb": "Destination hue range end angle in degrees",
                "min": 0.0,
                "max": 360.0,
                "default": 360.0,
            },
            {
                "name": "threshold",
                "type": "double",
                "nick": "Threshold",
                "blurb": "Gray threshold",
                "min": 0.0,
                "max": 1.0,
                "default": 0.0,
            },
        ],
    },
    "color-temperature": {
        "label": "Color _Temperature...",
        "name": "Color Temperature",
        "op": "gegl:color-temperature",
        "args": [
            {
                "name": "original-temperature",
                "type": "double",
                "nick": "Original Temperature (K)",
                "blurb": "Original color temperature of source in Kelvin",
                "min": 1000.0,
                "max": 12000.0,
                "default": 6500.0,
            },
            {
                "name": "intended-temperature",
                "type": "double",
                "nick": "Intended Temperature (K)",
                "blurb": "Desired color temperature in Kelvin",
                "min": 1000.0,
                "max": 12000.0,
                "default": 5500.0,
            },
        ],
    },
    "invert": {
        "label": "_Invert",
        "name": "Invert",
        "op": "gegl:invert-gamma",
        "args": [],
    },
    "sepia": {
        "label": "Se_pia...",
        "name": "Sepia",
        "op": "gegl:sepia",
        "args": [
            {
                "name": "scale",
                "type": "double",
                "nick": "Sepia Scale",
                "blurb": "Strength of sepia tone effect",
                "min": 0.0,
                "max": 2.0,
                "default": 1.0,
            },
            {
                "name": "srgb",
                "type": "boolean",
                "nick": "sRGB",
                "blurb": "Process in sRGB gamma space",
                "default": True,
            },
        ],
    },
    "color-to-gray": {
        "label": "_Black & White (Color to Gray)...",
        "name": "Black & White",
        "op": "gegl:c2g",
        "args": [
            {
                "name": "radius",
                "type": "int",
                "nick": "Radius",
                "blurb": "Neighborhood radius for local contrast computation",
                "min": 1,
                "max": 300,
                "default": 50,
            },
            {
                "name": "samples",
                "type": "int",
                "nick": "Samples",
                "blurb": "Number of samples per pixel",
                "min": 1,
                "max": 64,
                "default": 8,
            },
            {
                "name": "iterations",
                "type": "int",
                "nick": "Iterations",
                "blurb": "Number of refinement iterations",
                "min": 1,
                "max": 10,
                "default": 4,
            },
            {
                "name": "enhance-shadows",
                "type": "boolean",
                "nick": "Enhance Shadows",
                "blurb": "Enhance shadow details in grayscale output",
                "default": False,
            },
        ],
    },
    "threshold": {
        "label": "_Threshold...",
        "name": "Threshold",
        "op": "gegl:threshold",
        "args": [
            {
                "name": "value",
                "type": "double",
                "nick": "Threshold Level",
                "blurb": "Threshold cutoff value (0.0 to 1.0)",
                "min": 0.0,
                "max": 1.0,
                "default": 0.5,
            }
        ],
    },

    # --- Creative, Blur & Detail Adjustments ---
    "bloom": {
        "label": "_Bloom...",
        "name": "Bloom",
        "op": "gegl:bloom",
        "args": [
            {
                "name": "radius",
                "type": "double",
                "nick": "Radius",
                "blurb": "Glow blur radius in pixels",
                "min": 0.0,
                "max": 100.0,
                "default": 10.0,
            },
            {
                "name": "strength",
                "type": "double",
                "nick": "Strength",
                "blurb": "Glow strength",
                "min": 0.0,
                "max": 100.0,
                "default": 50.0,
            },
            {
                "name": "threshold",
                "type": "double",
                "nick": "Threshold",
                "blurb": "Highlight threshold",
                "min": 0.0,
                "max": 100.0,
                "default": 50.0,
            },
            {
                "name": "softness",
                "type": "double",
                "nick": "Softness",
                "blurb": "Bloom transition softness",
                "min": 0.0,
                "max": 100.0,
                "default": 25.0,
            },
            {
                "name": "limit-exposure",
                "type": "boolean",
                "nick": "Limit Exposure",
                "blurb": "Limit exposure of highlight glow",
                "default": False,
            },
        ],
    },
    "gaussian-blur": {
        "label": "Gaussian _Blur...",
        "name": "Gaussian Blur",
        "op": "gegl:gaussian-blur",
        "args": [
            {
                "name": "std-dev-x",
                "type": "double",
                "nick": "Size X",
                "blurb": "Standard deviation in horizontal direction (pixels)",
                "min": 0.0,
                "max": 100.0,
                "default": 5.0,
            },
            {
                "name": "std-dev-y",
                "type": "double",
                "nick": "Size Y",
                "blurb": "Standard deviation in vertical direction (pixels)",
                "min": 0.0,
                "max": 100.0,
                "default": 5.0,
            },
        ],
    },
    "high-pass": {
        "label": "_High Pass...",
        "name": "High Pass",
        "op": "gegl:high-pass",
        "args": [
            {
                "name": "std-dev",
                "type": "double",
                "nick": "Radius (Std Dev)",
                "blurb": "High pass filter radius in pixels",
                "min": 0.1,
                "max": 100.0,
                "default": 5.0,
            },
            {
                "name": "contrast",
                "type": "double",
                "nick": "Contrast",
                "blurb": "Contrast scaling factor",
                "min": 0.0,
                "max": 5.0,
                "default": 1.0,
            },
        ],
    },
    "unsharp-mask": {
        "label": "_Unsharp Mask (Sharpen)...",
        "name": "Unsharp Mask",
        "op": "gegl:unsharp-mask",
        "args": [
            {
                "name": "std-dev",
                "type": "double",
                "nick": "Radius (Std Dev)",
                "blurb": "Gaussian blur radius for unsharp masking in pixels",
                "min": 0.1,
                "max": 50.0,
                "default": 1.5,
            },
            {
                "name": "scale",
                "type": "double",
                "nick": "Amount / Scale",
                "blurb": "Sharpening intensity scaling factor",
                "min": 0.0,
                "max": 5.0,
                "default": 1.0,
            },
            {
                "name": "threshold",
                "type": "double",
                "nick": "Threshold",
                "blurb": "Minimum tonal difference to sharpen",
                "min": 0.0,
                "max": 1.0,
                "default": 0.0,
            },
        ],
    },
    "vignette": {
        "label": "Vi_gnette...",
        "name": "Vignette",
        "op": "gegl:vignette",
        "args": [
            {
                "name": "radius",
                "type": "double",
                "nick": "Radius",
                "blurb": "Vignette coverage radius proportion",
                "min": 0.0,
                "max": 2.0,
                "default": 1.0,
            },
            {
                "name": "softness",
                "type": "double",
                "nick": "Softness",
                "blurb": "Vignette edge softness",
                "min": 0.0,
                "max": 1.0,
                "default": 0.5,
            },
            {
                "name": "gamma",
                "type": "double",
                "nick": "Falloff Gamma",
                "blurb": "Falloff curve exponent",
                "min": 0.0,
                "max": 5.0,
                "default": 2.0,
            },
        ],
    },
}

# ============================================================================
# LAYER EFFECTS REGISTRY
# ============================================================================

LAYER_EFFECTS = {
    "stroke": {
        "label": "Stro_ke / Outline...",
        "name": "Stroke / Outline",
        "op": "gegl:dropshadow",
        "args": [
            {
                "name": "grow-radius",
                "type": "double",
                "nick": "Stroke Thickness (px)",
                "blurb": "Outline stroke thickness in pixels",
                "min": 0.0,
                "max": 100.0,
                "default": 4.0,
            },
            {
                "name": "opacity",
                "type": "double",
                "nick": "Opacity",
                "blurb": "Stroke opacity (0.0 to 1.0)",
                "min": 0.0,
                "max": 1.0,
                "default": 1.0,
            },
            {
                "name": "radius",
                "type": "double",
                "nick": "Blur Radius",
                "blurb": "Stroke edge blur radius",
                "min": 0.0,
                "max": 100.0,
                "default": 0.0,
            },
        ],
    },
    "drop-shadow": {
        "label": "_Drop Shadow...",
        "name": "Drop Shadow",
        "op": "gegl:dropshadow",
        "args": [
            {
                "name": "x",
                "type": "double",
                "nick": "Horizontal Offset (X)",
                "blurb": "Horizontal offset of shadow in pixels",
                "min": -200.0,
                "max": 200.0,
                "default": 10.0,
            },
            {
                "name": "y",
                "type": "double",
                "nick": "Vertical Offset (Y)",
                "blurb": "Vertical offset of shadow in pixels",
                "min": -200.0,
                "max": 200.0,
                "default": 10.0,
            },
            {
                "name": "radius",
                "type": "double",
                "nick": "Blur Radius",
                "blurb": "Shadow blur radius in pixels",
                "min": 0.0,
                "max": 100.0,
                "default": 10.0,
            },
            {
                "name": "opacity",
                "type": "double",
                "nick": "Opacity",
                "blurb": "Shadow opacity (0.0 to 1.0)",
                "min": 0.0,
                "max": 1.0,
                "default": 0.6,
            },
            {
                "name": "grow-radius",
                "type": "double",
                "nick": "Grow Radius / Spread",
                "blurb": "Grow shadow radius before blurring in pixels",
                "min": 0.0,
                "max": 100.0,
                "default": 0.0,
            },
        ],
    },
    "long-shadow": {
        "label": "_Long Shadow...",
        "name": "Long Shadow",
        "op": "gegl:long-shadow",
        "args": [
            {
                "name": "angle",
                "type": "double",
                "nick": "Angle (°)",
                "blurb": "Shadow projection angle in degrees",
                "min": 0.0,
                "max": 360.0,
                "default": 45.0,
            },
            {
                "name": "length",
                "type": "double",
                "nick": "Length (px)",
                "blurb": "Shadow length in pixels",
                "min": 0.0,
                "max": 1000.0,
                "default": 100.0,
            },
            {
                "name": "midpoint-rel",
                "type": "double",
                "nick": "Midpoint",
                "blurb": "Relative midpoint fade position (0.0 to 1.0)",
                "min": 0.0,
                "max": 1.0,
                "default": 0.5,
            },
        ],
    },
    "bevel": {
        "label": "_Bevel & Emboss...",
        "name": "Bevel & Emboss",
        "op": "gegl:bevel",
        "args": [
            {
                "name": "radius",
                "type": "double",
                "nick": "Radius / Size (px)",
                "blurb": "Bevel width radius in pixels",
                "min": 0.0,
                "max": 50.0,
                "default": 5.0,
            },
            {
                "name": "elevation",
                "type": "double",
                "nick": "Elevation (°)",
                "blurb": "Light elevation angle in degrees",
                "min": 0.0,
                "max": 90.0,
                "default": 25.0,
            },
            {
                "name": "depth",
                "type": "int",
                "nick": "Depth",
                "blurb": "Bevel depth percentage",
                "min": 1,
                "max": 100,
                "default": 40,
            },
            {
                "name": "azimuth",
                "type": "double",
                "nick": "Azimuth / Light Angle (°)",
                "blurb": "Light source direction angle in degrees",
                "min": 0.0,
                "max": 360.0,
                "default": 68.0,
            },
        ],
    },
    "inner-glow": {
        "label": "_Inner Glow...",
        "name": "Inner Glow",
        "op": "gegl:inner-glow",
        "args": [
            {
                "name": "radius",
                "type": "double",
                "nick": "Glow Radius (px)",
                "blurb": "Inner glow blur radius in pixels",
                "min": 0.0,
                "max": 100.0,
                "default": 10.0,
            },
            {
                "name": "grow-radius",
                "type": "double",
                "nick": "Grow Radius (px)",
                "blurb": "Inner glow grow radius in pixels",
                "min": 0.0,
                "max": 100.0,
                "default": 4.0,
            },
            {
                "name": "opacity",
                "type": "double",
                "nick": "Opacity",
                "blurb": "Inner glow opacity",
                "min": 0.0,
                "max": 2.0,
                "default": 1.0,
            },
        ],
    },
    "styles": {
        "label": "Layer _Styles (Multi-Effect)...",
        "name": "Layer Styles",
        "op": "gegl:styles",
        "args": [],
    },
}


# ============================================================================
# HELPER UTILITIES: GEGL AUTO-INSPECTION & EXTENSIBILITY
# ============================================================================

_GEGL_OP_CACHE = {}


def auto_inspect_gegl_args(op_name):
    """
    Auto-discovers properties of a GEGL operation if arguments are not
    explicitly declared. Returns a list of argument definitions.
    """
    if op_name in _GEGL_OP_CACHE:
        return _GEGL_OP_CACHE[op_name]

    args = []
    try:
        node = Gegl.Node()
        node.set_property("operation", op_name)
        op = node.get_gegl_operation()
        if not op:
            _GEGL_OP_CACHE[op_name] = args
            return args

        base_props = {
            "operation",
            "name",
            "gegl-operation",
            "dont-cache",
            "cache-policy",
            "use-opencl",
            "passthrough",
        }
        for pspec in GObject.list_properties(op):
            if pspec.name in base_props:
                continue

            ptype = pspec.value_type.name
            val_default = op.get_property(pspec.name)
            nick = pspec.get_nick() or pspec.name.replace("-", " ").title()
            blurb = pspec.get_blurb() or ""

            if ptype in ("gdouble", "gfloat"):
                min_v = float(getattr(pspec, "minimum", -100.0))
                max_v = float(getattr(pspec, "maximum", 100.0))
                if min_v < -1000.0:
                    min_v = -100.0
                if max_v > 1000.0:
                    max_v = 100.0
                args.append(
                    {
                        "name": pspec.name,
                        "type": "double",
                        "nick": nick,
                        "blurb": blurb,
                        "min": min_v,
                        "max": max_v,
                        "default": float(val_default if val_default is not None else 0.0),
                    }
                )
            elif ptype in ("gint", "guint", "glong", "gulong"):
                min_v = int(getattr(pspec, "minimum", 0))
                max_v = int(getattr(pspec, "maximum", 100))
                if min_v < -1000:
                    min_v = 0
                if max_v > 1000:
                    max_v = 100
                args.append(
                    {
                        "name": pspec.name,
                        "type": "int",
                        "nick": nick,
                        "blurb": blurb,
                        "min": min_v,
                        "max": max_v,
                        "default": int(val_default if val_default is not None else 0),
                    }
                )
            elif ptype == "gboolean":
                args.append(
                    {
                        "name": pspec.name,
                        "type": "boolean",
                        "nick": nick,
                        "blurb": blurb,
                        "default": bool(val_default if val_default is not None else False),
                    }
                )
    except Exception:
        pass

    _GEGL_OP_CACHE[op_name] = args
    return args


def get_effective_args(spec):
    """
    Returns explicit arguments if defined in the spec, otherwise
    falls back to auto-discovering from the GEGL operation.
    """
    if "args" in spec:
        return spec["args"]
    return auto_inspect_gegl_args(spec.get("op", ""))


# ============================================================================
# MAIN GIMP PLUG-IN CLASS
# ============================================================================

class AdjustmentLayer(Gimp.PlugIn):
    def do_set_i18n(self, procname):
        return True, "gimp30-python", None

    def do_query_procedures(self):
        procs = [ADJ_PREFIX + k for k in ADJUSTMENTS]
        procs.extend([FX_PREFIX + k for k in LAYER_EFFECTS])
        return procs

    def do_create_procedure(self, name):
        if name.startswith(ADJ_PREFIX):
            key = name[len(ADJ_PREFIX):]
            if key not in ADJUSTMENTS:
                return None
            return self._build_procedure(
                name=name,
                spec=ADJUSTMENTS[key],
                run_callback=self.run_adjustment,
                is_adjustment=True,
            )

        if name.startswith(FX_PREFIX):
            key = name[len(FX_PREFIX):]
            if key not in LAYER_EFFECTS:
                return None
            return self._build_procedure(
                name=name,
                spec=LAYER_EFFECTS[key],
                run_callback=self.run_layer_effect,
                is_adjustment=False,
            )

        return None

    def _build_procedure(self, name, spec, run_callback, is_adjustment=True):
        """Unified procedure constructor for adjustments and layer effects."""
        p = Gimp.ImageProcedure.new(
            self, name, Gimp.PDBProcType.PLUGIN, run_callback, None
        )
        p.set_image_types("*")

        if is_adjustment:
            p.set_sensitivity_mask(
                Gimp.ProcedureSensitivityMask.DRAWABLE
                | Gimp.ProcedureSensitivityMask.NO_DRAWABLES
            )
            p.set_documentation(
                f"Add {spec['name']} Adjustment Layer",
                f"Creates a non-destructive {spec['name']} adjustment layer with live interactive controls.",
                name,
            )
            # CRITICAL: set_menu_label MUST be called BEFORE add_menu_path!
            p.set_menu_label(spec.get("label", spec["name"]))
            p.set_attribution("GIMP Adjustment Layer Extension", "GPLv3", "2026")

            # Standard menu paths
            p.add_menu_path("<Image>/Layer/Adjustment Layer")
            p.add_menu_path("<Image>/Image/Adjustment Layer")
            p.add_menu_path("<Image>/Colors/Adjustment Layer")
        else:
            p.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.DRAWABLE)
            p.set_documentation(
                f"Apply {spec['name']} Layer Effect",
                f"Applies non-destructive {spec['name']} styling directly to the active layer.",
                name,
            )
            # CRITICAL: set_menu_label MUST be called BEFORE add_menu_path!
            p.set_menu_label(spec.get("label", spec["name"]))
            p.set_attribution("GIMP Adjustment Layer Extension", "GPLv3", "2026")

            p.add_menu_path("<Image>/Layer/Layer Effects")
            p.add_menu_path("<Image>/Filters/Layer Effects")

        # Register arguments for ProcedureDialog
        for arg in get_effective_args(spec):
            self._register_arg(p, arg)

        return p

    def _register_arg(self, proc, arg):
        atype = arg.get("type", "double")
        aname = arg["name"]
        anick = arg.get("nick", aname)
        ablurb = arg.get("blurb", "")

        if atype == "double":
            proc.add_double_argument(
                aname,
                anick,
                ablurb,
                arg.get("min", -100.0),
                arg.get("max", 100.0),
                arg.get("default", 0.0),
                GObject.ParamFlags.READWRITE,
            )
        elif atype == "int":
            proc.add_int_argument(
                aname,
                anick,
                ablurb,
                arg.get("min", 0),
                arg.get("max", 100),
                arg.get("default", 0),
                GObject.ParamFlags.READWRITE,
            )
        elif atype == "boolean":
            proc.add_boolean_argument(
                aname,
                anick,
                ablurb,
                arg.get("default", False),
                GObject.ParamFlags.READWRITE,
            )

    def _show_interactive_dialog(self, procedure, config, title, filter_obj, args_list):
        """Displays native ProcedureDialog with live updates on canvas."""
        GimpUi.init("adjustment-layer")
        dialog = GimpUi.ProcedureDialog.new(procedure, config, title)
        dialog.fill(None)

        # Hook config change notifications to update GEGL filter live
        if filter_obj and args_list:
            filter_config = filter_obj.get_config()
            def on_config_notify(cfg, pspec):
                self._transfer_config_properties(cfg, filter_config, args_list)
                filter_obj.update()
                Gimp.displays_flush()

            handler_id = config.connect("notify", on_config_notify)
        else:
            handler_id = None

        confirmed = bool(dialog.run())

        if handler_id and config.is_connected(handler_id):
            config.disconnect(handler_id)

        dialog.destroy()
        return confirmed

    def _transfer_config_properties(self, source_config, target_config, args_list):
        """Copies parameter values from procedure config to GEGL filter config."""
        if not (source_config and target_config and args_list):
            return
        for arg in args_list:
            pname = arg["name"]
            if source_config.find_property(pname) and target_config.find_property(pname):
                val = source_config.get_property(pname)
                try:
                    target_config.set_property(pname, val)
                except Exception:
                    pass

    def run_adjustment(self, procedure, run_mode, image, drawables, config, data):
        key = procedure.get_name()[len(ADJ_PREFIX):]
        if key not in ADJUSTMENTS:
            return procedure.new_return_values(
                Gimp.PDBStatusType.CALLING_ERROR,
                GLib.Error("Unknown adjustment layer procedure"),
            )

        adj = ADJUSTMENTS[key]
        args_list = get_effective_args(adj)

        # Determine target insertion position in the layer stack
        if drawables and len(drawables) > 0:
            target_layer = drawables[0]
            parent = target_layer.get_parent()
            position = image.get_item_position(target_layer)
        else:
            parent = None
            position = 0

        image.undo_group_start()
        try:
            # 1. Create a Pass-Through Layer Group
            group = Gimp.GroupLayer.new(image)
            group.set_name(f"{adj['name']} Adjustment")
            group.set_mode(Gimp.LayerMode.PASS_THROUGH)
            image.insert_layer(group, parent, position)

            # 2. Insert and keep a transparent blank base layer inside the group so the group
            # has full image bounds and GIMP's compositor evaluates the layer mask.
            img_w = image.get_width()
            img_h = image.get_height()
            blank_layer = Gimp.Layer.new(
                image,
                f"({adj['name']} Base)",
                img_w,
                img_h,
                Gimp.ImageType.RGBA_IMAGE,
                100.0,
                Gimp.LayerMode.NORMAL,
            )
            blank_layer.fill(Gimp.FillType.TRANSPARENT)
            image.insert_layer(blank_layer, group, 0)

            # 3. Create selection-aware mask on the layer group
            has_selection = not Gimp.Selection.is_empty(image)
            mask_type = (
                Gimp.AddMaskType.SELECTION
                if has_selection
                else Gimp.AddMaskType.WHITE
            )
            mask = group.create_mask(mask_type)
            group.add_mask(mask)

            # 4. Attach non-destructive GEGL filter to the layer group
            f = Gimp.DrawableFilter.new(group, adj["op"], adj["name"])
            self._transfer_config_properties(config, f.get_config(), args_list)
            group.append_filter(f)

            # 5. Keep group clean & collapsed
            group.set_expanded(False)

            # 6. Select the adjustment group
            image.set_selected_layers([group])
            Gimp.displays_flush()

            # 7. Interactive configuration dialog with live preview
            if run_mode == Gimp.RunMode.INTERACTIVE and args_list:
                if not self._show_interactive_dialog(
                    procedure, config, f"Adjustment: {adj['name']}", f, args_list
                ):
                    # Clean rollback on cancel
                    image.remove_layer(group)
                    image.undo_group_end()
                    Gimp.displays_flush()
                    return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, None)

        except Exception as e:
            image.undo_group_end()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR, GLib.Error(str(e))
            )

        image.undo_group_end()
        Gimp.displays_flush()
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, None)

    def run_layer_effect(self, procedure, run_mode, image, drawables, config, data):
        if not drawables:
            return procedure.new_return_values(
                Gimp.PDBStatusType.CALLING_ERROR,
                GLib.Error("No layer selected to apply layer effect"),
            )

        drawable = drawables[0]
        key = procedure.get_name()[len(FX_PREFIX):]
        if key not in LAYER_EFFECTS:
            return procedure.new_return_values(
                Gimp.PDBStatusType.CALLING_ERROR,
                GLib.Error("Unknown layer effect procedure"),
            )

        fx = LAYER_EFFECTS[key]
        args_list = get_effective_args(fx)

        image.undo_group_start()
        try:
            f = Gimp.DrawableFilter.new(drawable, fx["op"], fx["name"])
            self._transfer_config_properties(config, f.get_config(), args_list)
            drawable.append_filter(f)
            image.set_selected_layers([drawable])
            Gimp.displays_flush()

            # Interactive configuration dialog with live preview
            if run_mode == Gimp.RunMode.INTERACTIVE and args_list:
                if not self._show_interactive_dialog(
                    procedure, config, f"Layer Effect: {fx['name']}", f, args_list
                ):
                    f.delete()
                    image.undo_group_end()
                    Gimp.displays_flush()
                    return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, None)

        except Exception as e:
            image.undo_group_end()
            return procedure.new_return_values(
                Gimp.PDBStatusType.EXECUTION_ERROR, GLib.Error(str(e))
            )

        image.undo_group_end()
        Gimp.displays_flush()
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, None)


if __name__ == "__main__":
    Gimp.main(AdjustmentLayer.__gtype__, sys.argv)