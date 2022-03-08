import sys
sys.path.append("D:\\instance-segmentation\\")
sys.path.append("C:\\Users\\Admin\\AppData\\Roaming\\Python\\Python39\\site-packages\\")
sys.path.append("C:\\Users\\Admin\\AppData\\local\\programs\\python\\python39\\lib\\site-packages\\")

import os
import DataVars
import SetupPaths
import RealisticRenderer 
import ContourExtractor
import DepthGenerator
import DataExtractor

DataVars.count = 9

print("\n")
print("--Setup Paths--")
SetupPaths.set_base_path(os.getcwd()+ '//exported-data//')

print("\n")
print("--Realistic Render--")
RealisticRenderer.renderImage(DataVars.count)

print("\n")
print("--Contour Extraction--")
obj = ContourExtractor.extract(DataVars.count)

print("\n")
print("--Depth Generation--")
DepthGenerator.setup()
DepthGenerator.build()

print("\n")
print("--Data Extraction--")
DataExtractor.save(DataVars.count, obj)

print("Finished")