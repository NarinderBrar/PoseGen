import bpy
from math import tan
import bpy_extras
from mathutils import Matrix
from mathutils import Vector

import sys
sys.path.append(
    "c:\\users\\admin\\appdata\\local\\programs\\python\\python39\\lib\\site-packages")

from blenderMatrix import get_3x4_P_matrix_from_blender
import cv2

print(79*'-' + 3*'\n')

obj = bpy.data.objects['Cube']
scene = bpy.context.scene
mesh = obj.data

cam = bpy.data.objects['Camera']
P = get_3x4_P_matrix_from_blender(cam)
e1 = Vector((1, 0, 0, 1))
p1 = P * e1
p1 /= p1[2]
print("Projected e1")
print(p1)

path = r'C:\Users\Admin\Desktop\untitled.png'
image = cv2.imread(path)

center_coordinates = (int(0), int(0))
cv2.circle(image, center_coordinates, 1, (255, 0, 0), 2)
    
cv2.imshow('Image', image)