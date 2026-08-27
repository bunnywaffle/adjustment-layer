#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
Adjustment Layer & Layer Effects Plug-in for GIMP 3.0 / 3.2+
==============================================================================
Provides non-destructive Photoshop-style Adjustment Layers using Pass-Through
Layer Groups and GEGL filters with selection-aware layer masks, as well as
direct Non-Destructive Layer Effects.

All adjustments and effects are created instantly without custom modal
dialogs. Full interactive controls, live previews, and presets are handled
directly by GIMP 3's native Non-Destructive Editing (NDE) filter tools.

Menu Locations:
- Layer > Adjustment Layer > [Adjustment]
- Image > Adjustment Layer > [Adjustment]
- Colors > Adjustment Layer > [Adjustment]
- Layer > Layer Effects > [Effect]
- Filters > Layer Effects > [Effect]

------------------------------------------------------------------------------
HOW TO ADD NEW ADJUSTMENTS OR EFFECTS IN THE FUTURE:
------------------------------------------------------------------------------
Adding a new adjustment layer or layer effect takes just ONE single entry in
either ADJUSTMENTS or LAYER_EFFECTS below:

Example:
   "oilify": {
       "name": "Oilify",
       "op": "gegl:oilify",
       "label": "_Oilify",
       "defaults": {"mask-radius": 5},   # optional initial settings
   }
==============================================================================
"""

import sys
import gi

gi.require_version("Gimp", "3.0")
gi.require_version("Gegl", "0.4")
from gi.repository import Gimp, Gegl, GLib

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
        "label": "_Saturation",
        "name": "Saturation",
        "op": "gegl:saturation",
        "defaults": {"scale": 1.2},
    },
    "vibrance": {
        "label": "_Vibrance",
        "name": "Vibrance",
        "op": "gegl:vibrance",
        "defaults": {"vibrance": 0.25, "saturation": 1.0},
    },
    "exposure": {
        "label": "_Exposure",
        "name": "Exposure",
        "op": "gegl:exposure",
        "defaults": {"exposure": 0.0, "black-level": 0.0},
    },
    "brightness-contrast": {
        "label": "_Brightness-Contrast",
        "name": "Brightness-Contrast",
        "op": "gegl:brightness-contrast",
        "defaults": {"brightness": 0.0, "contrast": 1.0},
    },
    "levels": {
        "label": "_Levels",
        "name": "Levels",
        "op": "gegl:levels",
        "defaults": {"in-low": 0.0, "in-high": 1.0, "out-low": 0.0, "out-high": 1.0},
    },
    "curves": {
        "label": "_Curves (Contrast Curve)",
        "name": "Curves",
        "op": "gegl:contrast-curve",
        "defaults": {},
    },
    "hue-chroma": {
        "label": "Hue-_Saturation (Hue-Chroma)",
        "name": "Hue-Saturation",
        "op": "gegl:hue-chroma",
        "defaults": {"hue": 0.0, "chroma": 0.0, "lightness": 0.0},
    },
    "channel-mixer": {
        "label": "Channel _Mixer",
        "name": "Channel Mixer",
        "op": "gegl:mono-mixer",
        "defaults": {"preserve-luminosity": True, "red": 0.333, "green": 0.333, "blue": 0.333},
    },
    "color-rotate": {
        "label": "Color _Rotate",
        "name": "Color Rotate",
        "op": "gegl:color-rotate",
        "defaults": {"src-from": 0.0, "src-to": 360.0, "dest-from": 0.0, "dest-to": 360.0},
    },
    "color-temperature": {
        "label": "Color _Temperature",
        "name": "Color Temperature",
        "op": "gegl:color-temperature",
        "defaults": {"original-temperature": 6500.0, "intended-temperature": 5500.0},
    },
    "invert": {
        "label": "_Invert",
        "name": "Invert",
        "op": "gegl:invert-gamma",
        "defaults": {},
    },
    "sepia": {
        "label": "Se_pia",
        "name": "Sepia",
        "op": "gegl:sepia",
        "defaults": {"scale": 1.0, "srgb": True},
    },
    "color-to-gray": {
        "label": "_Black & White (Color to Gray)",
        "name": "Black & White",
        "op": "gegl:c2g",
        "defaults": {"radius": 50, "samples": 8, "iterations": 4},
    },
    "threshold": {
        "label": "_Threshold",
        "name": "Threshold",
        "op": "gegl:threshold",
        "defaults": {"value": 0.5},
    },

    # --- Creative, Blur & Detail Adjustments ---
    "bloom": {
        "label": "_Bloom",
        "name": "Bloom",
        "op": "gegl:bloom",
        "defaults": {"radius": 10.0, "strength": 50.0, "threshold": 50.0, "softness": 25.0},
    },
    "gaussian-blur": {
        "label": "Gaussian _Blur",
        "name": "Gaussian Blur",
        "op": "gegl:gaussian-blur",
        "defaults": {"std-dev-x": 5.0, "std-dev-y": 5.0},
    },
    "high-pass": {
        "label": "_High Pass",
        "name": "High Pass",
        "op": "gegl:high-pass",
        "defaults": {"std-dev": 5.0, "contrast": 1.0},
    },
    "unsharp-mask": {
        "label": "_Unsharp Mask (Sharpen)",
        "name": "Unsharp Mask",
        "op": "gegl:unsharp-mask",
        "defaults": {"std-dev": 1.5, "scale": 1.0, "threshold": 0.0},
    },
    "vignette": {
        "label": "Vi_gnette",
        "name": "Vignette",
        "op": "gegl:vignette",
        "defaults": {"radius": 1.0, "softness": 0.5, "gamma": 2.0},
    },
}

# ============================================================================
# LAYER EFFECTS REGISTRY
# ============================================================================

LAYER_EFFECTS = {
    "stroke": {
        "label": "Stro_ke / Outline",
        "name": "Stroke / Outline",
        "op": "gegl:dropshadow",
        "defaults": {
            "x": 0.0,
            "y": 0.0,
            "radius": 0.0,
            "grow-radius": 4.0,
            "opacity": 1.0,
        },
    },
    "drop-shadow": {
        "label": "_Drop Shadow",
        "name": "Drop Shadow",
        "op": "gegl:dropshadow",
        "defaults": {"x": 10.0, "y": 10.0, "radius": 10.0, "opacity": 0.6, "grow-radius": 0.0},
    },
    "long-shadow": {
        "label": "_Long Shadow",
        "name": "Long Shadow",
        "op": "gegl:long-shadow",
        "defaults": {"angle": 45.0, "length": 100.0, "midpoint-rel": 0.5},
    },
    "bevel": {
        "label": "_Bevel & Emboss",
        "name": "Bevel & Emboss",
        "op": "gegl:bevel",
        "defaults": {"radius": 5.0, "elevation": 25.0, "depth": 40, "azimuth": 68.0},
    },
    "inner-glow": {
        "label": "_Inner Glow",
        "name": "Inner Glow",
        "op": "gegl:inner-glow",
        "defaults": {"radius": 10.0, "grow-radius": 4.0, "opacity": 1.0},
    },
    "styles": {
        "label": "Layer _Styles (Multi-Effect)",
        "name": "Layer Styles",
        "op": "gegl:styles",
        "defaults": {},
    },
}


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
        """Builds a GIMP procedure with clean, instant execution."""
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
                f"Creates a non-destructive {spec['name']} adjustment layer with selection-aware mask.",
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

        return p

    def _apply_initial_defaults(self, filter_obj, defaults):
        """Applies initial default properties to the created GEGL filter."""
        if not filter_obj or not defaults:
            return
        config = filter_obj.get_config()
        if not config:
            return
        for prop_name, val in defaults.items():
            if config.find_property(prop_name):
                try:
                    config.set_property(prop_name, val)
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
            self._apply_initial_defaults(f, adj.get("defaults", {}))
            group.append_filter(f)

            # 5. Keep layer group collapsed for clean layer stack
            group.set_expanded(False)

            # 6. Select the adjustment group
            image.set_selected_layers([group])

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

        image.undo_group_start()
        try:
            f = Gimp.DrawableFilter.new(drawable, fx["op"], fx["name"])
            self._apply_initial_defaults(f, fx.get("defaults", {}))
            drawable.append_filter(f)
            image.set_selected_layers([drawable])

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