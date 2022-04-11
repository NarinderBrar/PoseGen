import bpy
import os
import cv2
import bmesh
import numpy as np
import DataVars as DataVars

from typing import List, Union, Tuple
from math import tan, radians
from mathutils import Vector, Matrix
from concurrent.futures import ThreadPoolExecutor
from itertools import repeat, chain

from shapely.ops import unary_union
from shapely.geometry import Point, Polygon, MultiPolygon

from bpy_extras.object_utils import world_to_camera_view as w2cv

def poly_union(polygons: List[Polygon], buffer: float) -> List[Polygon]:
    print("Applying union operation on poly")
    polygons = [poly.buffer(buffer) for poly in polygons]
    merged = unary_union(polygons)
    if isinstance(merged, MultiPolygon):
        polygons = [g for g in merged.geoms]
    else:
        polygons = [merged]

    polygons = [poly.buffer(-buffer) for poly in polygons]
    return polygons

def faces_to_polygons(face_set: List[List[Vector]]):
    print("Converting faces to polygons ...")
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

def project_mesh_on_camera(obj):
    print("Projecting mesh on the camera ...")
    cam = scene.camera
    cam_vec = cam.matrix_world.to_3x3() @ Vector((0, 0, -1))

    R = cam_vec.to_track_quat('-Z', 'Y').to_matrix().to_4x4()

    S = Matrix.Diagonal(
        Vector((1, (scene.render.resolution_y / scene.render.resolution_x), 1, 1)))

    T = Matrix.Translation((-0.5, -0.5, 0))

    obj.data.transform(obj.matrix_world)
    obj.matrix_world = Matrix()
    for v in obj.data.vertices:
        vec = w2cv(scene, cam, v.co)
        v.co = vec.x, vec.y, 0

    obj.data.transform(S @ T)
    obj.matrix_world = R

    angle_x = cam.data.angle_x
    x = (0.5 / tan(angle_x / 2)) * cam_vec.normalized()
    obj.matrix_world.translation = cam.matrix_world.translation + x

def drawMesh(face_sets) :
    print("Drawing mesh ..")
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

    bpy.context.collection.objects.link(obj)


def drawPoly(merged) :
    cam = context.scene.camera
    cam_vec = cam.matrix_world.to_3x3() @ Vector((0, 0, -1))

    R = cam_vec.to_track_quat('-Z', 'Y').to_matrix().to_4x4()
    S = Matrix.Diagonal(Vector((1, (scene.render.resolution_y / scene.render.resolution_x), 1, 1)))
    T = Matrix.Translation((-0.5, -0.5, 0))

    vertices = []
    for p in merged:
        if isinstance(p, MultiPolygon):
            for mulp in p.geoms:
                coords = list(mulp.exterior.coords)
                for mo in coords:
                    vertices.append((mo[0], mo[1], 0))
        else:
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

    bpy.context.collection.objects.link(obj)

    return obj

def get_face_sets(obj) -> List[List[Vector]]:
    print("Getting face sets ...")
    dg = context.evaluated_depsgraph_get()
    bmesh_ = bmesh.new()

    add_evaled_mesh(bmesh_, dg, obj, True)

    faces = []
    for face in bmesh_.faces:
        face_points = [obj.matrix_world.inverted() @ vert.co for vert in face.verts]
        face_points = [point.to_2d() for point in face_points]
        faces.append(face_points)
    bmesh_.free()

    return faces


def duplicate(obj, data=True, actions=True, collection=None):
    obj_copy = obj.copy()
    if data:
        obj_copy.data = obj_copy.data.copy()
    if actions and obj_copy.animation_data:
        obj_copy.animation_data.action = obj_copy.animation_data.action.copy()
    bpy.context.collection.objects.link(obj_copy)
    return obj_copy

def drawContour(obj, file, count):
    print("Drawing Contour")
    path = os.path.join(os.getcwd() + '//exported-data//', (file % count))
    image = cv2.imread(path)

    cam = context.scene.camera

    i =0
    Dict = {}
    pts = []
    for v in obj.data.vertices:
        x = g = float("{:.2f}".format(v.co.x))
        y = g = float("{:.2f}".format(v.co.y))
        if x in Dict.keys():
            if Dict[x]  == y:
                continue 
        co_2d = w2cv(scene, cam, obj.matrix_world @ v.co)
        render_scale = scene.render.resolution_percentage / 100
        render_size = (int(scene.render.resolution_x * render_scale),int(scene.render.resolution_y * render_scale),)
        center_coordinates = (int(co_2d.x * render_size[0]), int(render_size[1] - co_2d.y * render_size[1]))
        
        DataVars.points_2d.append((center_coordinates))
        pts.append([center_coordinates[0], center_coordinates[1]])

        image = cv2.circle(image, center_coordinates, 1, (255, 0, 0), 2)
        image = cv2.putText(image, str(i), center_coordinates, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
        Dict[x] = y
        i=i+1

    pathCont = os.path.join(os.getcwd() + '//exported-data//', ('renderContour-%d.png' % count))
    cv2.imwrite(pathCont, image)

    print(pts)
    pts = np.array(pts,np.int32)
    #pts = pts.reshape((-1, 1, 2))
    imagePoly = cv2.imread(path)
    imagePoly = cv2.fillPoly(imagePoly, [pts], (255, 0, 0))

    pathPoly = os.path.join(os.getcwd() + '//exported-data//', ('renderSegmentaion-%d.png' % count))
    cv2.imwrite(pathPoly, imagePoly)
    print(path)

def extract(count): 
    print("Start extracting contour ...")

    file = 'realistic-%d.png'
    types = ["MESH","SURFACE"]
    targets = [o for o in context.selected_objects if o.type in types]

    if not isinstance(targets, list):
        targets = [targets]

    if not targets:
        print("Select mesh or surface")
        return

    obj = targets[0]
    obj.select_set(False)
    obj_copy = duplicate(obj=obj, data=True, actions=True)
    obj_copy.select_set(True)

    project_mesh_on_camera(obj_copy)

    face_sets = [get_face_sets(obj_copy)]
    poly_sets = [faces_to_polygons(face_set) for face_set in face_sets]

    with ThreadPoolExecutor() as executor:
        buffer = 0.00001
        merged_sets = executor.map(poly_union, poly_sets, repeat(buffer))

    merged = list(chain.from_iterable(merged_sets))

    objs = bpy.data.objects
    objs.remove(obj_copy, do_unlink=True)

    obj_outline = drawPoly(merged)

    drawContour(obj_outline, file, count)
    objs.remove(obj_outline, do_unlink=True)

    obj.select_set(True)

    return obj

context = bpy.context
scene = context.scene