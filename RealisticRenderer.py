import os
import bpy

def renderImage(count):
    file = 'realistic-%d.png'
    path = os.path.join(os.getcwd()+ '//exported-data//', (file % count))
    scene = bpy.data.scenes[0]
    render = scene.render
    render.filepath = path
    render.image_settings.file_format = "PNG"
    render.image_settings.compression = 15

    print("Rendering realistic image:", file)
    print("Render Engine:", render.engine)

    bpy.ops.render.render(write_still=True)