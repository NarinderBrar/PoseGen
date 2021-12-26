from bpy.types import Panel
from bpy.utils import register_class, unregister_class

from .operators import EXPORT_OT_Export_Outline_SVG


class VIEW3D_PT_Outline_To_SVG(Panel):
    bl_label = "Outline to SVG"
    bl_idname = "VIEW3D_PT_outline_to_svg"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Outline To SVG"

    def draw(self, context):
        addon_props = context.scene.outline_to_svg_props

        layout = self.layout
        col = layout.column(align=True)
        row = col.row(align=True)
        row.label(text="Export")
        row = col.row(align=True)
        row.prop(addon_props, "filepath", text="")
        row = col.row(align=True)
        btn = row.operator(
            EXPORT_OT_Export_Outline_SVG.bl_idname,
            text="Export SVG"
        )
        btn.filepath = addon_props.filepath


def register():
    register_class(VIEW3D_PT_Outline_To_SVG)


def unregister():
    unregister_class(VIEW3D_PT_Outline_To_SVG)
