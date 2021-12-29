import bpy
import bpy
import bmesh
from bpy.props import StringProperty
from typing import List, Union, Tuple
from concurrent.futures import ThreadPoolExecutor

from mathutils import Vector, Matrix
import numpy as np

from itertools import repeat, chain

from shapely.ops import unary_union
from shapely.geometry import Point, Polygon, MultiPolygon

from typing import List, Tuple
from mathutils import Matrix, Vector

from bpy_extras.view3d_utils import (
    location_3d_to_region_2d,
    region_2d_to_location_3d,
    region_2d_to_origin_3d,
    region_2d_to_vector_3d,
)

def poly_union(polygons: List[Polygon], buffer: float) -> List[Polygon]:
    """ Perform union on list of polygons with buffer for cleaning incorrect alignments """
    # Buffer to increase overlay
    polygons = [poly.buffer(buffer) for poly in polygons]

    # Perform merge
    merged = unary_union(polygons)

    # Account for multipolygon output
    if isinstance(merged, MultiPolygon):
        polygons = [g for g in merged.geoms]
    else:
        polygons = [merged]

    # Remove buffer
    polygons = [poly.buffer(-buffer) for poly in polygons]

    return polygons

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

def avg_vectors(vectors: List[Vector]):
    nvectors = len(vectors)
    total = None
    for v in vectors:
        if total is None:
            total = v.copy()
            continue
        total += v

    return total / nvectors

def view3d_find():
    # returns first 3d view, normally we get from context
    for area in bpy.context.window.screen.areas:
        if area.type == 'VIEW_3D':
            v3d = area.spaces[0]
            rv3d = v3d.region_3d
            for region in area.regions:
                if region.type == 'WINDOW':
                    return region, rv3d
    return None, None

def view3d_camera_border(scene):
    obj = scene.camera
    cam = obj.data

    frame = cam.view_frame(scene=scene)

    # move from object-space into world-space 
    frame = [obj.matrix_world @ v for v in frame]

    # move into pixelspace
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    region, rv3d = view3d_find()
    frame_px = [location_3d_to_region_2d(region, rv3d, v) for v in frame]
    return frame_px

def add_evaled_mesh(bm, dg: bpy.types.Depsgraph, obj: bpy.types.Object, to_world: bool = True):
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
        #face_points = [vert.co for vert in face.verts]
        # flip = Vector((1, -1))
        face_points = [point.to_2d() for point in face_points]
        # print(face_points)

        # Correct flip
        for p in face_points:
            p.y *= -1

        faces.append(face_points)
    bm.free()

    return faces

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

def translate_face_set(face_set: List[List[Vector]], xy):
    translated = []
    for face in face_set:
        translated.append([v + xy for v in face])

    return translated

def execute(context: bpy.types.Context): 
    valid_target_types = ["MESH","SURFACE","CURVE","META","FONT"]
    targets = [o for o in context.selected_objects if o.type in valid_target_types]

    if not targets:
        print("No valid targets selected")
        return

    area = context.area
    rv3d = area.spaces[0].region_3d
    view_rotation = rv3d.view_rotation
    invert_view_rot = view_rotation.to_matrix().to_4x4().inverted()

    face_sets = [get_flattened_faces(context, obj, invert_view_rot) for obj in targets]

    # origin_offset = None
    # view_frame = get_camera_frame(context, invert_view_rot, flatten=True)
    # for v in view_frame:
    #     v.y *= -1
    #     if origin_offset is None:
    #         origin_offset = v.copy()
    #         continue
    #     origin_offset.x = min(origin_offset.x, v.x)
    #     origin_offset.y = min(origin_offset.y, v.y)
    
    # loc_correction = origin_offset * -1
    # view_frame = [loc_correction + v for v in view_frame]
    
    # frame_px = view3d_camera_border(bpy.context.scene)
    # frame_origin = avg_vectors(view_frame)

    poly_sets = [faces_to_polygons(face_set) for face_set in face_sets]

    with ThreadPoolExecutor() as executor:
        buffer = 0.00001
        merged_sets = executor.map(poly_union, poly_sets, repeat(buffer))

    merged = list(chain.from_iterable(merged_sets))
    #print(merged)

    #svg_bounds = process_geo.get_bbox(merged)
    #units = self.get_units_string(context)

    # Make position and origin relative
    # face_sets = [translate_face_set(face_set, loc_correction) for face_set in face_sets]
    # face_set = face_sets[0]
    # face = face_set[0]

    vertices = []
    for p in merged:
        print(p.exterior.coords)
        #for k in p:
        coords = list(p.exterior.coords)
        for mo in coords:
            vertices.append((mo[0], mo[1], 0))

    edges = []
    faces = []
    new_mesh = bpy.data.meshes.new('new_mesh')
    new_mesh.from_pydata(vertices, edges, faces)
    new_mesh.update()
    new_object = bpy.data.objects.new('new_object', new_mesh)
    new_collection = bpy.data.collections.new('new_collection')
    bpy.context.scene.collection.children.link(new_collection)
    new_collection.objects.link(new_object)

context = bpy.context
scene = context.scene

execute(context)
print("Finished")