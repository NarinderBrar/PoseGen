import sys
sys.path.append(
    "C:\\Users\\Narinder\\AppData\\Roaming\\Python\\Python39\\site-packages\\")

sys.path.append(
    "C:\\Users\\Narinder\\AppData\\local\\programs\\python\\python39\\lib\\site-packages\\")

import bpy
import os
import random

class Renderer:
    def init(self):
        self.count = 0

    def renderImage(self, file):
        self.path = os.path.join(os.getcwd(), (file % self.count))
        scene = bpy.data.scenes[0]
        render = scene.render
        render.filepath = self.path
        render.image_settings.file_format = "PNG"
        render.image_settings.compression = 15
        print("Rendering image:",file)
        print("Render Engine:", render.engine)
        bpy.ops.render.render(write_still=True)

    def renderNormal(self):
        file = 'realistic%d.png'
        self.renderImage(file)

    def renderSemantic(self):
        file = 'semantic%d.png'
        object = bpy.data.objects['Cube']
        object.location = (random.random() * -18, random.random() * 18, random.random() * 3 + 2)
        object["inst_id"] = 1
        r = random.uniform(0, 90)
        object.rotation_euler = (r, r, r)
        self.renderImage(file)

r = Renderer()
r.init()
r.renderNormal()
r.renderSemantic()
print("Finished")