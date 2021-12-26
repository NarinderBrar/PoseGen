import bpy

from bpy import context
from mathutils import Matrix, Vector
from math import tan, radians
from bpy_extras.object_utils import world_to_camera_view as w2cv

def tocam(scene, obs):
    cam = scene.camera
    cam_vec = cam.matrix_world.to_3x3() @ Vector((0, 0, -1))
    R = cam_vec.to_track_quat('-Z', 'Y').to_matrix().to_4x4()

    s = Vector((1, (scene.render.resolution_y / scene.render.resolution_x), 1, 1))
    # scale based on resolution
    S = Matrix.Diagonal(s)
    # translate such that origin is middle point of image (and hence cam)
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
        if cam.data.type == 'ORTHO':
            ob.scale *= cam.data.ortho_scale


bpy.ops.object.duplicate()
tocam(context.scene, context.selected_objects)
