import bpy
import numpy as np
from mathutils import Matrix
import os
import DataVars

import skimage
from skimage import io

ImageWidth = 1920
ImageHeight = 1080

ox = ImageWidth/2
oy = ImageHeight/2

fx = 588
fy = 588

K = np.array([[fx, 0, ox], [0, fy, oy], [0, 0, 1]], dtype=np.float32)
Kinv = np.linalg.inv(K)

CameraFOV = 50
MaxDepth = 1500 #cmeters ?
DepthScale = 100

EXT = '.png'

def set_camera_fov(fov):
    global CameraFOV
    CameraFOV = fov

def set_scale(scale):
    global DepthScale
    DepthScale = scale

def set_image_width_and_height(width, height):
    global ImageWidth
    global ImageHeight
    global ox
    global oy
    global K
    global Kinv

    ImageWidth = width
    ImageHeight = height

    ox = ImageWidth/2
    oy = ImageHeight/2

    K = np.array([[fx, 0, ox], [0, fy, oy], [0, 0, 1]], dtype=np.float32)
    Kinv = np.linalg.inv(K)

def set_depth_threshold(threshold):
    global MaxDepth
    MaxDepth = threshold

def set_camera_properties(camera_name="Camera", inv_camera=True):
    camera = bpy.data.cameras[camera_name]
    camera.type = 'PERSP'
    camera.lens_unit = 'FOV'
    #camera.angle = np.radians(CameraFOV)
    #camera.sensor_fit = 'AUTO'
    #camera.sensor_width = 32.0
    # clip start/end in unit defined by Scene Should be meters
    camera.clip_start = 0.1  # meters
    camera.clip_end = 100  # meters
    if inv_camera:
        print("InvertCamera is True", inv_camera)
        bpy.data.objects[camera_name].scale = 1, -1, -1


def set_renderer_properties(scene):
    print(scene.render.engine, type(scene.render.engine))
    scene.render.engine = 'CYCLES'
    scene.render.resolution_x = ImageWidth
    scene.render.resolution_y = ImageHeight
    scene.render.resolution_percentage = 100

def set_scene_properties(scene_name='Scene'):
    scene = bpy.data.scenes[scene_name]
    set_renderer_properties(scene)
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.system_rotation = 'RADIANS'

def get_camera(camera_name='Camera'):
    return bpy.data.cameras[camera_name]

def get_camera_as_object(camera_name='Camera'):
    return bpy.data.objects[camera_name]

def get_camera_transformation(camera_name='Camera'):
    camera = get_camera_as_object(camera_name)
    return camera.matrix_world

def update_scene(scene='Scene'):
    bpy.data.scenes[scene].update()

def build_nodes():
    print("building nodes")

    bpy.context.scene.use_nodes = True
    tree = bpy.context.scene.node_tree
    links = tree.links

    # clear default nodes
    for n in tree.nodes:
        tree.nodes.remove(n)

    # create input render layer node
    rl = tree.nodes.new('CompositorNodeRLayers')
    rl.location = 185,285

    # create output node
    v = tree.nodes.new('CompositorNodeViewer')
    v.location = 750,80
    v.use_alpha = False

    multiplier = tree.nodes.new('CompositorNodeMapValue')
    multiplier.location = 450, 80
    multiplier.size[0] = 1000

    outputNodeZbuffer = tree.nodes.new('CompositorNodeOutputFile')
    outputNodeZbuffer.location = 750,185
    outputNodeZbuffer.base_path = DataVars.BasePath + DataVars.EXRDepthPath
    RGBFileNameFormat = 'depth-'+ str(DataVars.count)+"-"
    outputNodeZbuffer.file_slots[0].path = RGBFileNameFormat 
    outputNodeZbuffer.file_slots[0].use_node_format = False
    outputNodeZbuffer.file_slots[0].format.file_format = "OPEN_EXR"
    outputNodeZbuffer.file_slots[0].format.color_mode = 'RGB'
    outputNodeZbuffer.file_slots[0].format.color_depth = '32'

    # Links
    links.new(rl.outputs[2], multiplier.inputs[0])
    links.new(multiplier.outputs[0], v.inputs[0])  # link Image output to Viewer input
    links.new(rl.outputs[2], outputNodeZbuffer.inputs[0])

def get_depth_map():
    pixels = bpy.data.images['Viewer Node'].pixels

    depthMap = np.zeros((ImageHeight, ImageWidth), dtype=np.uint16)
    zBuffer = np.array(pixels[:])

    for c in range(0, ImageWidth):
        for r in range(0, ImageHeight):
            index = r * ImageWidth * 4 + c * 4
            red = zBuffer[index]
            green = zBuffer[index + 1]
            blue = zBuffer[index + 2]
            alpha = zBuffer[index + 3]

            if (red != green or green != blue):
                print("Failed", alpha, red, green, blue)
                return;

            depth = red
            if(depth > MaxDepth):
                depth = 0

            v = np.array([c, r, 1], dtype=np.float32)
            n = Kinv.dot(v)
            n = n / np.linalg.norm(n);
            n = n * depth

            depthMap[ImageHeight - 1 - r, c] = np.uint16(n[2] * DepthScale)

    return depthMap

def save_data(depth_map):
    depthName = str(DataVars.count) + '.png'
    depthMap = depth_map

    print(DataVars.BasePath)
    io.imsave(DataVars.BasePath + DataVars.DepthPath + depthName, skimage.img_as_uint(depthMap))

def animation(render=False):
    bpy.ops.render.render(animation=False)
    depthMap = get_depth_map()

    return depthMap

def setup():
    set_camera_fov(CameraFOV)
    set_scale(DepthScale)

    set_image_width_and_height(ImageWidth, ImageHeight)
    set_depth_threshold(DepthScale * 1000) # meters -> converted to mm

    build_nodes()

    set_camera_properties(inv_camera=False)
    set_scene_properties()

def build():
    print('Building depth maps...')

    depth_map = animation(render=True)
    save_data(depth_map)

    print('Depth images saved')