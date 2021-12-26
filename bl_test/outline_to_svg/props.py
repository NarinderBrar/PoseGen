import bpy
from bpy.types import PropertyGroup
from bpy.utils import register_class, unregister_class
from bpy.props import (
    StringProperty,
    PointerProperty,
)


class Outlines_To_SVG_Properties(PropertyGroup):
    """ Addon panel UI properties """

    filepath: StringProperty(name="Output Path", subtype="FILE_PATH")


def register():
    register_class(Outlines_To_SVG_Properties)

    bpy.types.Scene.outline_to_svg_props = PointerProperty(
        type=Outlines_To_SVG_Properties
    )

def unregister():
    del bpy.types.Scene.outline_to_svg_props 
    unregister_class(Outlines_To_SVG_Properties)

