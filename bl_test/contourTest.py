import sys
sys.path.append(
    "C:\\Users\\Narinder\\AppData\\Roaming\\Python\\Python39\\site-packages\\")

sys.path.append(
    "C:\\Users\\Narinder\\AppData\\local\\programs\\python\\python39\\lib\\site-packages\\")

import numpy as np
import os

import cv2 as ocv

file = 'renderId100.png'
path = os.path.join(os.getcwd(), (file))
image = ocv.imread(path)

img_gray = ocv.cvtColor(
    image, ocv.COLOR_BGR2GRAY)
ret, thresh = ocv.threshold(img_gray, 1, 255, ocv.THRESH_BINARY)

contours, hierarchy = ocv.findContours(
    image=thresh, mode=ocv.RETR_TREE, method=ocv.CHAIN_APPROX_SIMPLE)

file = 'render100.png'
path = os.path.join(os.getcwd(), (file))
contour = ocv.imread(path)
ocv.drawContours(image=contour, contours=contours, contourIdx=-1,
                 color=(0, 255, 0), thickness=2, lineType=ocv.LINE_AA)


ocv.imshow("", thresh)
