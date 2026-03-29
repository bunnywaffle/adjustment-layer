#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gi

gi.require_version("Gimp", "3.0")
gi.require_version("GimpUi", "3.0")
gi.require_version("Gtk", "3.0")
from gi.repository import Gimp
from gi.repository import GimpUi
from gi.repository import Gtk
from gi.repository import GLib
import sys

PLUG_IN_PROC_PREFIX = "plug-in-adjustment-layer-"

ADJUSTMENTS = {
    # Colors
    "hue-saturation": {
        "label": "_Hue-Saturation",
        "name": "Hue-Saturation",
        "op": "gimp:hue-saturation",
    },
    "color-balance": {
        "label": "_Color Balance",
        "name": "Color Balance",
        "op": "gimp:color-balance",
    },
    "brightness-contrast": {
        "label": "_Brightness-Contrast",
        "name": "Brightness-Contrast",
        "op": "gimp:brightness-contrast",
    },
    "levels": {
        "label": "_Levels",
        "name": "Levels",
        "op": "gimp:levels",
    },
    "curves": {
        "label": "Cu_rves",
        "name": "Curves",
        "op": "gimp:curves",
    },
    "exposure": {
        "label": "_Exposure",
        "name": "Exposure",
        "op": "gegl:exposure",
    },
    "colorize": {
        "label": "Colori_ze",
        "name": "Colorize",
        "op": "gimp:colorize",
    },
    "channel-mixer": {
        "label": "Channel Mi_xer",
        "name": "Channel Mixer",
        "op": "gegl:channel-mixer",
    },
    "shadows-highlights": {
        "label": "_Shadows-Highlights",
        "name": "Shadows-Highlights",
        "op": "gegl:shadows-highlights",
    },
    "color-exchange": {
        "label": "Color E_xchange",
        "name": "Color Exchange",
        "op": "gegl:color-exchange",
    },
    "vibrance": {
        "label": "_Vibrance",
        "name": "Vibrance",
        "op": "gegl:vibrance",
    },
    "invert": {
        "label": "_Invert",
        "name": "Invert",
        "op": "gegl:invert-gamma",
    },
    # Blur
    "blur": {
        "label": "_Gaussian Blur",
        "name": "Gaussian Blur",
        "op": "gegl:gaussian-blur",
    },
    # Light and Shadow
    "bloom": {
        "label": "_Bloom",
        "name": "Bloom",
        "op": "gegl:bloom",
    },
    "lens-flare": {
        "label": "_Lens Flare",
        "name": "Lens Flare",
        "op": "gegl:lens-flare",
    },
    "vignette": {
        "label": "_Vignette",
        "name": "Vignette",
        "op": "gegl:vignette",
    },
}


class AdjustmentLayer(Gimp.PlugIn):
    def do_query_procedures(self):
        return [PLUG_IN_PROC_PREFIX + key for key in ADJUSTMENTS]

    def do_create_procedure(self, name):
        key = name[len(PLUG_IN_PROC_PREFIX) :]
        if key not in ADJUSTMENTS:
            return None

        adj = ADJUSTMENTS[key]

        procedure = Gimp.ImageProcedure.new(
            self, name, Gimp.PDBProcType.PLUGIN, self.run, None
        )
        procedure.set_image_types("*")
        procedure.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.DRAWABLE)
        procedure.set_menu_label(adj["label"])
        procedure.set_attribution("Adjustment Layer", "Adjustment Layer", "2025")
        procedure.add_menu_path("<Image>/Adjustment Layer")
        procedure.set_documentation(
            f"Add {adj['name']} Adjustment Layer",
            f"Creates a non-destructive {adj['name']} adjustment layer",
            name,
        )
        return procedure

    def run(self, procedure, run_mode, image, drawables, config, data):
        if not drawables:
            return procedure.new_return_values(
                Gimp.PDBStatusType.CALLING_ERROR,
                GLib.Error("No drawable selected."),
            )

        drawable = drawables[0]

        key = procedure.get_name()[len(PLUG_IN_PROC_PREFIX) :]
        if key not in ADJUSTMENTS:
            return procedure.new_return_values(
                Gimp.PDBStatusType.CALLING_ERROR,
                GLib.Error(f"Unknown adjustment: {key}"),
            )

        adj = ADJUSTMENTS[key]
        parent = drawable.get_parent()
        position = image.get_item_position(drawable)

        image.undo_group_start()

        try:
            group = Gimp.GroupLayer.new(image)
            group.set_name(adj["name"])
            group.set_mode(Gimp.LayerMode.PASS_THROUGH)
            image.insert_layer(group, parent, position)

            try:
                f = Gimp.DrawableFilter.new(group, adj["op"], adj["name"])
                group.append_filter(f)
            except Exception:
                image.remove_layer(group)
                return procedure.new_return_values(
                    Gimp.PDBStatusType.CALLING_ERROR,
                    GLib.Error(f"Filter '{adj['op']}' not available."),
                )

            # Show GEGL filter properties dialog
            f_config = f.get_config()
            proc = Gimp.get_pdb().lookup_procedure(adj["op"])
            if proc is not None:
                GimpUi.init(PLUG_IN_PROC_PREFIX)
                dlg_config = proc.create_config()
                for arg in proc.get_arguments():
                    pname = arg.get_name()
                    try:
                        val = f_config.get_property(pname)
                        dlg_config.set_property(pname, val)
                    except Exception:
                        pass
                dlg = GimpUi.ProcedureDialog.new(proc, dlg_config, adj["name"])
                dlg.fill(None)
                cancelled = not dlg.run()
                # Copy dialog values back to filter config
                if not cancelled:
                    for arg in proc.get_arguments():
                        pname = arg.get_name()
                        try:
                            val = dlg_config.get_property(pname)
                            f_config.set_property(pname, val)
                        except Exception:
                            pass
                    f.update()
                dlg.destroy()
                if cancelled:
                    image.remove_layer(group)
                    return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, None)

            try:
                p = Gimp.get_pdb().lookup_procedure("gimp-selection-is-empty")
                c = p.create_config()
                c.set_property("image", image)
                result = p.run(c)
                if not result.index(1):
                    mask = group.create_mask(Gimp.AddMaskType.SELECTION)
                    group.add_mask(mask)
                    pn = Gimp.get_pdb().lookup_procedure("gimp-selection-none")
                    cn = pn.create_config()
                    cn.set_property("image", image)
                    pn.run(cn)
                else:
                    mask = group.create_mask(Gimp.AddMaskType.WHITE)
                    group.add_mask(mask)
            except Exception:
                mask = group.create_mask(Gimp.AddMaskType.WHITE)
                group.add_mask(mask)

            group.set_expanded(False)

        finally:
            image.undo_group_end()

        Gimp.displays_flush()
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, None)


Gimp.main(AdjustmentLayer.__gtype__, sys.argv)
