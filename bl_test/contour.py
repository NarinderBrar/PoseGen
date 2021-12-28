import bpy
from bpy.props import StringProperty

from typing import List, Union, Tuple
import sys

import bpy
import bmesh
from bpy_extras.view3d_utils import (
    location_3d_to_region_2d,
    region_2d_to_location_3d,
    region_2d_to_origin_3d,
    region_2d_to_vector_3d,
)
from mathutils import Vector, Matrix
import numpy as np

from shapely.geometry import Polygon


def add_evaled_mesh(
    bm, dg: bpy.types.Depsgraph, obj: bpy.types.Object, to_world: bool = True
):
    object_eval = obj.evaluated_get(dg)
    mesh_from_eval = object_eval.to_mesh()
    if to_world:
        for v in mesh_from_eval.vertices:
            v.co = object_eval.matrix_world @ v.co

    bm.from_mesh(mesh_from_eval)

    # Remove temporary mesh.
    object_eval.to_mesh_clear()
    return None

def get_flattened_faces(context, targets: Union[List[bpy.types.Object], bpy.types.Object], transform: Matrix) -> List[List[Vector]]:
    if not isinstance(targets, list):
        targets = [targets]

    dg = context.evaluated_depsgraph_get()

    bm = bmesh.new()

    for obj in targets:
        # Added all targeted objects
        add_evaled_mesh(bm, dg, obj, True)

    faces = []

    for face in bm.faces:
        face_points = [transform @ vert.co for vert in face.verts]
        # flip = Vector((1, -1))
        face_points = [point.to_2d() for point in face_points]
        # print(face_points)

        # Correct flip
        for p in face_points:
            p.y *= -1

        faces.append(face_points)
    bm.free()

    return faces

def execute(context: bpy.types.Context): 
    valid_target_types = [
        "MESH",
        "SURFACE",
        "CURVE",
        "META",
        "FONT",
    ]

    targets = [o for o in context.selected_objects if o.type in valid_target_types]

    if not targets:
        print("No valid targets selected")
        return {"CANCELLED"}

    area = context.area
    rv3d = area.spaces[0].region_3d
    view_rotation = rv3d.view_rotation

    invert_view_rot = view_rotation.to_matrix().to_4x4().inverted()

    face_sets = [get_flattened_faces(context, obj, invert_view_rot) for obj in targets]

    # # Set origin
    # # find min-x min-y
    # origin_offset = None
    # if self.is_camera_projector(context):
    #     view_frame = get_geo.get_camera_frame(
    #         context, invert_view_rot, flatten=True
    #     )
    #     for v in view_frame:
    #         v.y *= -1  # Note: Ugh
    #         if origin_offset is None:
    #             origin_offset = v.copy()
    #             continue
    #         origin_offset.x = min(origin_offset.x, v.x)
    #         origin_offset.y = min(origin_offset.y, v.y)

    # else:
    #     for face_set in face_sets:
    #         for face in face_set:
    #             for v in face:
    #                 if origin_offset is None:
    #                     origin_offset = v.copy()
    #                     continue
    #                 origin_offset.x = min(origin_offset.x, v.x)
    #                 origin_offset.y = min(origin_offset.y, v.y)

    # loc_correction = origin_offset * -1
    # # print("\n\nloc correct\t", loc_correction)

    # # Cancel offset
    # if self.is_camera_projector(context):
    #     view_frame = [loc_correction + v for v in view_frame]

    # # Make position and origin relative
    # face_sets = [
    #     process_geo.translate_face_set(face_set, loc_correction)
    #     for face_set in face_sets
    # ]

    # if self.is_camera_projector(context):
    #     frame_origin = get_geo.avg_vectors(view_frame)
    # else:
    #     frame_origin = get_geo.get_face_sets_origin(face_sets)

    # # Convert targets to shapely polygons
    # poly_sets = [get_geo.faces_to_polygons(
    #     face_set) for face_set in face_sets]

    # # Perform union operation
    # with ThreadPoolExecutor() as executor:
    #     # buffer = 0.001
    #     buffer = 0.00001
    #     merged_sets = executor.map(
    #         process_geo.poly_union, poly_sets, repeat(buffer)
    #     )

    # # Flatten merged face sets
    # merged = list(chain.from_iterable(merged_sets))

    # if not self.is_camera_projector(context):
    #     svg_bounds = process_geo.get_bbox(merged)
    #     # print('svg bounds:\t', svg_bounds)
    # else:
    #     # Get camera frame
    #     # print('cam bound:\t', view_frame)
    #     cam_projection_bounds = [view_frame[2], view_frame[0]]

    #     svg_bounds = (
    #         cam_projection_bounds[0].to_tuple()
    #         + cam_projection_bounds[1].to_tuple()
    #     )

    # units = self.get_units_string(context)

    # write_geo.write_poly_to_svg(
    #     self.filepath, merged, svg_bounds[:2], svg_bounds[2:], units
    # )
    # return {"FINISHED"}


context = bpy.context
scene = context.scene
execute(context)