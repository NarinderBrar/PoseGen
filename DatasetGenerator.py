import sys
sys.path.append("D:\\instance-segmentation\\")
sys.path.append("C:\\Users\\Admin\\AppData\\Roaming\\Python\\Python39\\site-packages\\")
sys.path.append("C:\\Users\\Admin\\AppData\\local\\programs\\python\\python39\\lib\\site-packages\\")

import SetupPaths
import RealisticRenderer 
import ContourExtractor
import DepthGenerator
import DataExtractor

count = 5

print("\n")
print("--Setup Paths--")
SetupPaths.set_base_path("\\exported-data\\")

print("\n")
print("--Realistic Render--")
RealisticRenderer.renderImage(count)

print("\n")
print("--Contour Extraction--")
ContourExtractor.extract(count)

print("\n")
print("--Depth Generation--")
DepthGenerator.setup()
DepthGenerator.build()

print("\n")
print("--Data Extraction--")
DataExtractor.save(count)

print("Finished")