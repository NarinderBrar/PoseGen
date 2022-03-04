import sys

#sys.path.append("C:\\Users\\Narinder\\AppData\\Roaming\\Python\\Python39\\site-packages\\")
sys.path.append("C:\\Users\\Admin\\AppData\\Roaming\\Python\\Python39\\site-packages\\")

#sys.path.append("C:\\Users\\Narinder\\AppData\\local\\programs\\python\\python39\\lib\\site-packages\\")
sys.path.append("C:\\Users\\Admin\\AppData\\Local\\Programs\\Python\\Python39\\Lib\\site-packages\\")

import bpy
from mathutils import Matrix

import datavars as datavars

def get_camera_as_object(camera_name='Camera'):
    return bpy.data.objects[camera_name]

def get_camera_transformation(camera_name='Camera'):
    camera = get_camera_as_object(camera_name)
    return camera.matrix_world

def animation():
    translation = mathutils.Vector()
    rotation = mathutils.Matrix.Rotation(0, 3, 'X')

    T = get_camera_transformation()

    translation = T.to_translation()
    rotation = T.to_3x3()

    translation = mathutils.Vector(translation)
    rotation = rotation.to_quaternion()

    return translation, rotation, 0
    
def save_data(translation=None, rotation=None):
    datavars.groundTruth.append("%.4f" % translation.x)
    datavars.groundTruth.append("%.4f" % translation.y)
    datavars.groundTruth.append("%.4f" % translation.z)
    
    datavars.groundTruth.append("%.4f" % rotation.x)
    datavars.groundTruth.append("%.4f" % rotation.y)
    datavars.groundTruth.append("%.4f" % rotation.z)
    datavars.groundTruth.append("%.4f" % rotation.w) 

    # ground_truth.write("%.4f" % translation.x + ' ' + "%.4f" % translation.y + ' ' + "%.4f" % translation.z + ' ' + "%.4f" % rotation.x + ' ' + "%.4f" % rotation.y + ' ' + "%.4f" % rotation.z + ' ' + "%.4f" % rotation.w + '\n')
    # ground_truth.close()

def get_calibration_matrix_K_from_blender(camd):
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

    datavars.groundTruth.append(alpha_u) 
    datavars.groundTruth.append(skew) 
    datavars.groundTruth.append(u_0) 
    datavars.groundTruth.append(0)             
    datavars.groundTruth.append(alpha_v)    
    datavars.groundTruth.append(v_0)    
    datavars.groundTruth.append(0)     
    datavars.groundTruth.append(0) 
    datavars.groundTruth.append(1) 

    return K

def runapp():
    depth_map, translation, rotation, timestamp = animation(render=True)
    save_data(depth_map, translation, rotation, timestamp)