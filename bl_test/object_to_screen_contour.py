import bpy
import bmesh
from typing import List, Union, Tuple

from math import tan, radians
from mathutils import Vector, Matrix
from concurrent.futures import ThreadPoolExecutor
from itertools import repeat, chain

from shapely.ops import unary_union
from shapely.geometry import Point, Polygon, MultiPolygon

from bpy_extras.object_utils import world_to_camera_view as w2cv

def poly_union(polygons: List[Polygon], buffer: float) -> List[Polygon]:
    polygons = [poly.buffer(buffer) for poly in polygons]
    merged = unary_union(polygons)
    if isinstance(merged, MultiPolygon):
        polygons = [g for g in merged.geoms]
    else:
        polygons = [merged]

    polygons = [poly.buffer(-buffer) for poly in polygons]
    return polygons

def faces_to_polygons(face_set: List[List[Vector]]):
    polygons = []

    for face in face_set:
        pts = []
        for point in face:
            pts.append(point.to_tuple())

        polygon = Polygon(pts)
        polygons.append(polygon)
    return polygons

def add_evaled_mesh(bm, dg: bpy.types.Depsgraph, obj: bpy.types.Object, to_world: bool = True):
    object_eval = obj.evaluated_get(dg)
    mesh_from_eval = object_eval.to_mesh()
    if to_world:
        for v in mesh_from_eval.vertices:
            v.co = object_eval.matrix_world @ v.co

    bm.from_mesh(mesh_from_eval)
    object_eval.to_mesh_clear()
    return None

def tocam(scene, obs):
    cam = scene.camera
    cam_vec = cam.matrix_world.to_3x3() @ Vector((0, 0, -1))
    R = cam_vec.to_track_quat('-Z', 'Y').to_matrix().to_4x4()

    s = Vector((1, (scene.render.resolution_y / scene.render.resolution_x), 1, 1))
    S = Matrix.Diagonal(s)

    T = Matrix.Translation((-0.5, -0.5, 0))

    for ob in obs:
        ob.data.transform(ob.matrix_world)
        ob.matrix_world = Matrix()
        for v in ob.data.vertices:
            vec = w2cv(scene, cam, v.co)
            v.co = vec.x, vec.y, 0

        ob.data.transform(S @ T)

        ob.matrix_world = R
        angle_x = cam.data.angle_x
        x = (0.5 / tan(angle_x / 2)) * cam_vec.normalized()
        ob.matrix_world.translation = cam.matrix_world.translation + x

def drawMesh(face_sets, context) :
    cam = context.scene.camera
    cam_vec = cam.matrix_world.to_3x3() @ Vector((0, 0, -1))
    R = cam_vec.to_track_quat('-Z', 'Y').to_matrix().to_4x4()

    S = Matrix.Diagonal(Vector((1, (scene.render.resolution_y / scene.render.resolution_x), 1, 1)))

    T = Matrix.Translation((-0.5, -0.5, 0))

    vertices = []
    for face_set in face_sets:
        for face in face_set:
            for v in face:
                vertices.append((v[0], v[1], 0))

    edges = []
    faces = []
    new_mesh = bpy.data.meshes.new('new_mesh')
    new_mesh.from_pydata(vertices, edges, faces)
    new_mesh.update()

    obj = bpy.data.objects.new('obj', new_mesh)
   
    obj.matrix_world = R
    angle_x = cam.data.angle_x
    x = (0.5 / tan(angle_x / 2)) * cam_vec.normalized()
    obj.matrix_world.translation = cam.matrix_world.translation + x

    new_collection = bpy.data.collections.new('coll')
    bpy.context.scene.collection.children.link(new_collection)
    new_collection.objects.link(obj)

def drawPoly(merged) :
    cam = context.scene.camera
    cam_vec = cam.matrix_world.to_3x3() @ Vector((0, 0, -1))

    R = cam_vec.to_track_quat('-Z', 'Y').to_matrix().to_4x4()
    S = Matrix.Diagonal(Vector((1, (scene.render.resolution_y / scene.render.resolution_x), 1, 1)))
    T = Matrix.Translation((-0.5, -0.5, 0))

    vertices = []
    for p in merged:
        coords = list(p.exterior.coords)
        for mo in coords:
            vertices.append((mo[0], mo[1], 0))

    edges = []
    faces = []
    new_mesh = bpy.data.meshes.new('new_mesh')
    new_mesh.from_pydata(vertices, edges, faces)
    new_mesh.update()

    obj = bpy.data.objects.new('obj', new_mesh)
   
    obj.matrix_world = R
    angle_x = cam.data.angle_x
    x = (0.5 / tan(angle_x / 2)) * cam_vec.normalized()
    obj.matrix_world.translation = cam.matrix_world.translation + x

    new_collection.objects.link(obj)

def get_flattened_faces(context, obj) -> List[List[Vector]]:
    dg = context.evaluated_depsgraph_get()
    bm = bmesh.new()

    add_evaled_mesh(bm, dg, obj, True)

    faces = []
    for face in bm.faces:
        face_points = [obj.matrix_world.inverted() @ vert.co for vert in face.verts]
        face_points = [point.to_2d() for point in face_points]
        faces.append(face_points)
    bm.free()

    return faces
    
def execute(context: bpy.types.Context): 
    valid_target_types = ["MESH","SURFACE","CURVE","META","FONT"]
    targets = [o for o in context.selected_objects if o.type in valid_target_types]

    if not isinstance(targets, list):
        targets = [targets]

    if not targets:
        print("No valid targets selected")
        return

    bpy.ops.object.duplicate()

    collision_object = bpy.context.scene.objects.active
    for cl_o in collision_object:
        new_collection2.objects.link(cl_o)

    tocam(context.scene, context.selected_objects)

    for obj in targets:
        print (obj)
        face_sets = [get_flattened_faces(context, obj)]
        poly_sets = [faces_to_polygons(face_set) for face_set in face_sets]

        with ThreadPoolExecutor() as executor:
            buffer = 0.00001
            merged_sets = executor.map(poly_union, poly_sets, repeat(buffer))

        merged = list(chain.from_iterable(merged_sets))

        drawPoly(merged)

context = bpy.context
scene = context.scene

new_collection = bpy.data.collections.new('coll')
bpy.context.scene.collection.children.link(new_collection)

new_collection2 = bpy.data.collections.new('coll2')
bpy.context.scene.collection.children.link(new_collection2)

execute(context)
print("Finished")