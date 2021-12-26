# Built-ins
import os
from concurrent.futures import ThreadPoolExecutor
from itertools import repeat, chain
import sys

# Blender Built-ins
import bpy
from bpy.props import StringProperty
from bpy.utils import register_class, unregister_class

from . import get_geo
from . import write_geo
from . import process_geo
from .consts import METRIC_UNITS, IMPERIAL_UNITS


class EXPORT_OT_Export_Outline_SVG(bpy.types.Operator):
    bl_idname = "export_mesh.export_outline_svg"
    bl_label = "Export Outline to SVG"
    bl_options = {"REGISTER", "INTERNAL"}

    filepath: StringProperty(name="Output Path", subtype="FILE_PATH")

    @classmethod
    def poll(cls, context):
        return all((len(context.selected_objects) != 0, context.area.type == "VIEW_3D"))

    def get_region_view_type(self, context):
        """ return one of [‘PERSP’, ‘ORTHO’, ‘CAMERA’] """
        area = context.area
        rv3d = area.spaces[0].region_3d
        return rv3d.view_perspective

    def is_valid_projector(self, context):
        if self.get_region_view_type(context) == "ORTHO":
            return True
        if self.get_region_view_type(context) == "CAMERA":
            return context.scene.camera.data.type == "ORTHO"
        return False

    def is_camera_projector(self, context):
        return self.get_region_view_type(context) == "CAMERA"

    def get_units_string(self, context):
        user_units = context.scene.unit_settings.length_unit
        unit_sys = context.scene.unit_settings.system
        if unit_sys == "METRIC" and user_units in METRIC_UNITS.keys():
            return METRIC_UNITS[user_units]
        elif unit_sys == "IMPERIAL" and user_units in IMPERIAL_UNITS.keys():
            return IMPERIAL_UNITS[user_units]
        else:
            return ""

    def validate_filepath(self):
        if self.filepath == "":
            self.report({"WARNING"}, "No filepath selected")
            return {"CANCELLED"}

        # Ensure valid filepath
        self.filepath = bpy.path.abspath(self.filepath)

        if os.path.isdir(self.filepath):
            self.filepath = os.path.join(self.filepath, "svg_export.svg")

        self.filepath = bpy.path.ensure_ext(self.filepath, ".svg")

    def execute(self, context: bpy.types.Context):
        self.validate_filepath()

        if not self.is_valid_projector(context):
            self.report({"WARNING"}, "Only Orthographic views are supported")
            return {"CANCELLED"}

        valid_target_types = [
            "MESH",
            "SURFACE",
            "CURVE",
            "META",
            "FONT",
        ]

        targets = [o for o in context.selected_objects if o.type in valid_target_types]
        if not targets:
            self.report({"WARNING"}, "No valid targets selected")
            return {"CANCELLED"}

        area = context.area
        rv3d = area.spaces[0].region_3d
        view_rotation = rv3d.view_rotation

        invert_view_rot = view_rotation.to_matrix().to_4x4().inverted()

        face_sets = [
            get_geo.get_flattened_faces(context, obj, invert_view_rot)
            for obj in targets
        ]

        # Set origin
        # find min-x min-y
        origin_offset = None
        if self.is_camera_projector(context):
            view_frame = get_geo.get_camera_frame(
                context, invert_view_rot, flatten=True
            )
            for v in view_frame:
                v.y *= -1  # Note: Ugh
                if origin_offset is None:
                    origin_offset = v.copy()
                    continue
                origin_offset.x = min(origin_offset.x, v.x)
                origin_offset.y = min(origin_offset.y, v.y)

        else:
            for face_set in face_sets:
                for face in face_set:
                    for v in face:
                        if origin_offset is None:
                            origin_offset = v.copy()
                            continue
                        origin_offset.x = min(origin_offset.x, v.x)
                        origin_offset.y = min(origin_offset.y, v.y)

        loc_correction = origin_offset * -1
        # print("\n\nloc correct\t", loc_correction)

        # Cancel offset
        if self.is_camera_projector(context):
            view_frame = [loc_correction + v for v in view_frame]

        # Make position and origin relative
        face_sets = [
            process_geo.translate_face_set(face_set, loc_correction)
            for face_set in face_sets
        ]

        if self.is_camera_projector(context):
            frame_origin = get_geo.avg_vectors(view_frame)
        else:
            frame_origin = get_geo.get_face_sets_origin(face_sets)

        # Convert targets to shapely polygons
        poly_sets = [get_geo.faces_to_polygons(face_set) for face_set in face_sets]

        # Perform union operation
        with ThreadPoolExecutor() as executor:
            # buffer = 0.001
            buffer = 0.00001
            merged_sets = executor.map(
                process_geo.poly_union, poly_sets, repeat(buffer)
            )

        # Flatten merged face sets
        merged = list(chain.from_iterable(merged_sets))

        if not self.is_camera_projector(context):
            svg_bounds = process_geo.get_bbox(merged)
            # print('svg bounds:\t', svg_bounds)
        else:
            # Get camera frame
            # print('cam bound:\t', view_frame)
            cam_projection_bounds = [view_frame[2], view_frame[0]]

            svg_bounds = (
                cam_projection_bounds[0].to_tuple()
                + cam_projection_bounds[1].to_tuple()
            )

        units = self.get_units_string(context)

        write_geo.write_poly_to_svg(
            self.filepath, merged, svg_bounds[:2], svg_bounds[2:], units
        )
        return {"FINISHED"}


def register():
    register_class(EXPORT_OT_Export_Outline_SVG)


def unregister():
    unregister_class(EXPORT_OT_Export_Outline_SVG)
