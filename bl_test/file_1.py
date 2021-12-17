import sys
sys.path.append(
    "C:\\Users\\Admin\\AppData\\Roaming\\Python\\Python39\\site-packages\\")

sys.path.append(
    "C:\\Users\\Admin\\AppData\\local\\programs\\python\\python39\\lib\\site-packages\\")

#C:\Users\Admin\AppData\Local\Programs\Python\Python39\Lib\site-packages

import numpy as np
import bpy
import os

import cv2 as ocv
import bpycv as bcv
import random

import json
from json import JSONEncoder

class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)

class Renderer:

    def init(self):
        self.count = 101
        self.result = None

    def change(self):

        object = bpy.data.objects['obj']
        object.location = (random.random() * -18,
                           random.random() * 18, random.random() * 3 + 2)
        object["inst_id"] = 1001

        r = random.uniform(0, 90)
        object.rotation_euler = (r, r, r)

        object = bpy.data.objects['Sphere']
        object.location = (random.random() * -18,
                           random.random() * 18, random.random() *  4 + 1)
        object["inst_id"] = 2000

        r = random.uniform(0,90)
        object.rotation_euler = (r, r, r)

        object = bpy.data.objects['Cube']
        object.location = (random.random() * -18,
                           random.random() * 18, random.random() * 6)
        object["inst_id"] = 3000

        r = random.uniform(0, 90)
        object.rotation_euler = (r, r, r)

    def render(self):
        self.result = bcv.render_data()

        dir = '//'
        file = 'render%d.png'
        path = os.path.join(os.getcwd(), (file % self.count))
        ocv.imwrite(path, self.result["image"][..., ::-1])

        file = 'renderId%d.png'
        path = os.path.join(os.getcwd(), (file % self.count))
        ocv.imwrite(path, np.uint16(self.result["inst"]))

        image = ocv.imread(path)

        img_gray = ocv.cvtColor(
            image, ocv.COLOR_BGR2GRAY)
        ret, thresh = ocv.threshold(img_gray, 3, 255, ocv.THRESH_BINARY_INV)

        contours, hierarchy = ocv.findContours(
            image=thresh, mode=ocv.RETR_TREE, method=ocv.CHAIN_APPROX_SIMPLE)

        contour = self.result["image"][..., ::-1].copy()
        ocv.drawContours(image=contour, contours=contours, contourIdx=-1,
                         color=(0, 255, 0), thickness=2, lineType=ocv.LINE_AA)

        file = 'renderMask%d.png'
        path = os.path.join(os.getcwd(), (file % self.count))
        ocv.imwrite(path, thresh)

        font = ocv.FONT_HERSHEY_COMPLEX

        pointsList = []

        for cnt in contours:
            approx = ocv.approxPolyDP(cnt, 0.009 * ocv.arcLength(cnt, True), True)

            n = approx.ravel()
            i = 0

            for j in n:
                if(i % 2 == 0):
                    x = n[i]
                    y = n[i + 1]
                    pointsList.append((x, y))
                i = i + 1

        file = 'renderContour%d.png'
        path = os.path.join(os.getcwd(), (file % self.count))
        ocv.imwrite(path, contour)

        npData = {"array": np.array(pointsList)}
        encodedNPData = json.dumps(npData, cls=NumpyArrayEncoder)
        
        file = 'contour%d.json'
        path = os.path.join(os.getcwd(), (file % self.count))
        with open(path, "w") as outfile:
            outfile.write(encodedNPData)

        self.count = self.count + 1

r = Renderer()
r.init()

for i in range (1):
    r.change()
    r.render()
    print("Finished")