import sys

import bpy
import mathutils
from mathutils import Matrix

import DataVars as DataVars
import JSONWriter as jsonwriter

def get_camera_as_object(camera_name='Camera'):
    return bpy.data.objects[camera_name]

def get_camera_transformation(camera_name='Camera'):
    camera = get_camera_as_object(camera_name)
    return camera.matrix_world

def getTR():
    translation = mathutils.Vector()
    rotation = mathutils.Matrix.Rotation(0, 3, 'X')

    T = get_camera_transformation()

    translation = T.to_translation()
    rotation = T.to_3x3()

    translation = mathutils.Vector(translation)
    rotation = rotation.to_quaternion()

    return translation, rotation
    
def save_ground_truth(translation=None, rotation=None):
    DataVars.groundTruth.append("%.4f" % translation.x)
    DataVars.groundTruth.append("%.4f" % translation.y)
    DataVars.groundTruth.append("%.4f" % translation.z)
    
    DataVars.groundTruth.append("%.4f" % rotation.x)
    DataVars.groundTruth.append("%.4f" % rotation.y)
    DataVars.groundTruth.append("%.4f" % rotation.z)
    DataVars.groundTruth.append("%.4f" % rotation.w) 

def save_calibration_matrix_K(camd):
    f_in_mm = camd.lens
    scene = bpy.context.scene

    resolution_x_in_px = scene.render.resolution_x
    resolution_y_in_px = scene.render.resolution_y

    scale = scene.render.resolution_percentage / 100

    sensor_width_in_mm = camd.sensor_width
    sensor_height_in_mm = camd.sensor_height

    pixel_aspect_ratio = scene.render.pixel_aspect_x / scene.render.pixel_aspect_y

    if camd.sensor_fit == 'VERTICAL':
        s_u = resolution_x_in_px * scale / sensor_width_in_mm / pixel_aspect_ratio
        s_v = resolution_y_in_px * scale / sensor_height_in_mm
    else: # 'HORIZONTAL' and 'AUTO'
        pixel_aspect_ratio = scene.render.pixel_aspect_x / scene.render.pixel_aspect_y
        s_u = resolution_x_in_px * scale / sensor_width_in_mm
        s_v = resolution_y_in_px * scale * pixel_aspect_ratio / sensor_height_in_mm

    # Parameters of intrinsic calibration matrix K
    alpha_u = f_in_mm * s_u
    alpha_v = f_in_mm * s_v

    u_0 = resolution_x_in_px*scale / 2
    v_0 = resolution_y_in_px*scale / 2

    skew = 0

    K = Matrix(
        ((alpha_u, skew,    u_0),
        (0 ,  alpha_v, v_0),
        (0 ,    0,      1)))

    DataVars.cameraMatrix.append(alpha_u) 
    DataVars.cameraMatrix.append(skew) 
    DataVars.cameraMatrix.append(u_0) 
    DataVars.cameraMatrix.append(0)             
    DataVars.cameraMatrix.append(alpha_v)    
    DataVars.cameraMatrix.append(v_0)    
    DataVars.cameraMatrix.append(0)     
    DataVars.cameraMatrix.append(0) 
    DataVars.cameraMatrix.append(1) 

    return K

def save(count):
    translation, rotation = getTR()

    save_ground_truth(translation, rotation)
    save_calibration_matrix_K(bpy.data.objects['Camera'].data)

    jsonwriter.writeJSON(count)

