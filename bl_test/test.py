import bpy
import bmesh
from mathutils import Vector, Matrix
from typing import List, Union, Tuple

context = bpy.context
area = context.area
rv3d = area.spaces[0].region_3d
view_rotation = rv3d.view_rotation

invert_view_rot = view_rotation.to_matrix().to_4x4().inverted()

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
        # flip = Vector((1, -1))
        face_points = [point.to_2d() for point in face_points]
        # print(face_points)

        # Correct flip
        for p in face_points:
            p.y *= -1

        faces.append(face_points)
    bm.free()

    return faces

valid_target_types = ["MESH","SURFACE","CURVE","META","FONT",]
targets = [o for o in context.selected_objects if o.type in valid_target_types]
face_sets = [get_flattened_faces(context, obj, invert_view_rot) for obj in targets]