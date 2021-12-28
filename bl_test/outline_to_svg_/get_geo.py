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

def get_flattened_faces(
    context, targets: Union[List[bpy.types.Object], bpy.types.Object], transform: Matrix
) -> List[List[Vector]]:
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


def faces_to_polygons(face_set: List[List[Vector]]):
    """ Convert list of face points to shapely polyon """
    polygons = []
    for face in face_set:

        pts = []
        for point in face:
            # TODO: Hacky fix, find actual source of problem
            # point.y *= -1
            pts.append(point.to_tuple())
        # pts.append(face[-1])

        polygon = Polygon(pts)
        polygons.append(polygon)

    return polygons


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


def get_point_in_screenspace(co: Vector, context):
    area = context.area
    region = area.regions[5]
    rv3d = area.spaces[0].region_3d
    return location_3d_to_region_2d(region, rv3d, co, default=None)


def get_camera_frame(context, transform: Matrix, flatten: bool) -> Polygon:
    # Apply camera crop
    camera = context.scene.camera
    cam_frame_local = camera.data.view_frame()

    # Apply frame aspect ration
    width = context.scene.render.resolution_x
    height = context.scene.render.resolution_y

    if width > height:
        aspect_correction = Vector((1.0, height / width, 1.0))
    else:
        aspect_correction = Vector((width / height, 1.0, 1.0))
    for v in cam_frame_local:
        v *= aspect_correction

    cam_frame_world = [camera.matrix_world @ v for v in cam_frame_local]
    cam_frame_world = [transform @ v for v in cam_frame_world]
    if flatten:
        cam_frame_world = [pt.to_2d() for pt in cam_frame_world]

    return cam_frame_world


def get_camera_normal(context) -> Vector:
    area = context.area
    region = area.regions[5]
    rv3d = area.spaces[0].region_3d
    width = region.width
    height = region.height

    viewport_center = Vector((width / 2, height / 2))
    cam_normal = region_2d_to_vector_3d(region, rv3d, viewport_center)
    return cam_normal


def get_objects_centroid(objects: List[bpy.types.Object]) -> Vector:
    bound_maximums = get_bounds_of_objects(objects)
    bound_center = (bound_maximums[0] + bound_maximums[1]) * 0.5
    return bound_center


def get_bounds_of_objects(objects) -> Tuple[Vector, Vector]:
    """ Return maximum bounding box of objects pair of vectors (vMin, vMax) """
    bound_points_world = []
    for obj in objects:
        # Get each objects bounding box point in world space and append to bound_points_world
        bound_points_local = [Vector(point) for point in obj.bound_box]
        bound_points_world += [obj.matrix_world @ point for point in bound_points_local]

    # Convert to numpy array and get min, max values for each axis
    bound_points_world = np.array(bound_points_world)
    x_values = bound_points_world[:, 0]
    y_values = bound_points_world[:, 1]
    z_values = bound_points_world[:, 2]

    # Get extremes
    x_min, x_max = x_values.min(), x_values.max()
    y_min, y_max = y_values.min(), y_values.max()
    z_min, z_max = z_values.min(), z_values.max()

    # Generate output vectors
    v_min = Vector((x_min, y_min, z_min))
    v_max = Vector((x_max, y_max, z_max))

    return (v_min, v_max)


def get_face_sets_origin(face_sets):
    points = []
    for face_set in face_sets:
        for face in face_set:
            for v in face:
                points.append(v)

    return avg_vectors(points)


def avg_vectors(vectors: List[Vector]):
    nvectors = len(vectors)
    total = None
    for v in vectors:
        if total is None:
            total = v.copy()
            continue
        total += v

    return total / nvectors
