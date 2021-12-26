import sys
sys.path.append(
    "C:\\Users\\Narinder\\AppData\\Roaming\\Python\\Python39\\site-packages\\")

sys.path.append(
    "C:\\Users\\Narinder\\AppData\\local\\programs\\python\\python39\\lib\\site-packages\\")


import alphashape

import bpy
import bpy_extras
from mathutils import Matrix
from mathutils import Vector

import cv2

def get_calibration_matrix_K_from_blender(camd):
    f_in_mm = camd.lens
    scene = bpy.context.scene
    resolution_x_in_px = scene.render.resolution_x
    resolution_y_in_px = scene.render.resolution_y

    scale = scene.render.resolution_percentage / 100

    sensor_width_in_mm = camd.sensor_width
    sensor_height_in_mm = camd.sensor_height

    pixel_aspect_ratio = scene.render.pixel_aspect_x / scene.render.pixel_aspect_y
    if (camd.sensor_fit == 'VERTICAL'):
        s_u = resolution_x_in_px * scale / sensor_width_in_mm / pixel_aspect_ratio 
        s_v = resolution_y_in_px * scale / sensor_height_in_mm
    else:
        pixel_aspect_ratio = scene.render.pixel_aspect_x / scene.render.pixel_aspect_y
        s_u = resolution_x_in_px * scale / sensor_width_in_mm
        s_v = resolution_y_in_px * scale * pixel_aspect_ratio / sensor_height_in_mm
    
    alpha_u = f_in_mm * s_u
    alpha_v = f_in_mm * s_v

    u_0 = resolution_x_in_px * scale / 2
    v_0 = resolution_y_in_px * scale / 2

    skew = 0

    K = Matrix(
        ((alpha_u, skew, u_0),
        (0, alpha_v, v_0),
        (0, 0, 1 )))
    return K

def get_3x4_RT_matrix_from_blender(cam):
    R_bcam2cv = Matrix(
        ((1, 0,  0),
         (0, -1, 0),
         (0, 0, -1)))

    location, rotation = cam.matrix_world.decompose()[0:2]
    R_world2bcam = rotation.to_matrix().transposed()

    T_world2bcam = -1*R_world2bcam @ location

    R_world2cv = R_bcam2cv@R_world2bcam
    T_world2cv = R_bcam2cv@T_world2bcam

    RT = Matrix((
        R_world2cv[0][:] + (T_world2cv[0],),
        R_world2cv[1][:] + (T_world2cv[1],),
        R_world2cv[2][:] + (T_world2cv[2],)
         ))

    return RT

def get_3x4_P_matrix_from_blender(cam):
    K = get_calibration_matrix_K_from_blender(cam.data)
    RT = get_3x4_RT_matrix_from_blender(cam)
    return K@RT, K, RT

def project_by_object_utils(cam, point):
    scene = bpy.context.scene
    co_2d = bpy_extras.object_utils.world_to_camera_view(scene, cam, point)
    render_scale = scene.render.resolution_percentage / 100
    render_size = (int(scene.render.resolution_x * render_scale),int(scene.render.resolution_y * render_scale),)
    return Vector((co_2d.x * render_size[0], render_size[1] - co_2d.y * render_size[1]))

cam = bpy.data.objects['Camera']

P, K, RT = get_3x4_P_matrix_from_blender(cam)

obj = bpy.data.objects['Suzanne']
mesh = obj.data

path = r'.\..\image.png'
image = cv2.imread(path)

location, rotation, scale = obj.matrix_world.decompose()
R = rotation.to_matrix().transposed()

print(location)
print(rotation)
print(scale)

points = []
for v in mesh.vertices:
    e1 = v.co.copy()

    e1 = scale * e1

    p1 = P @ e1
    p1 /= p1[2]
    center_coordinates = (int(p1[0]), int(p1[1]))
    points.append((center_coordinates[0], center_coordinates[1]))
    #image = cv2.circle(image, center_coordinates, 1, (255, 0, 0), 2)

#alpha = 0. * alphashape.optimizealpha(points)
hull = alphashape.alphashape(points, 0.015)
print(dir(hull.exterior))

xp = hull.exterior.xy[0]
yp = hull.exterior.xy[1]
for i in range (len(xp)):
    center_coordinates = (int(xp[i]), int(yp[i]))
    #image = cv2.circle(image, center_coordinates, 3, (0, 0, 255), 4)
    image = cv2.putText(image, str(i), center_coordinates,
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)

cv2.imshow('Image', image)