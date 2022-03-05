import os
import DataVars

def set_base_path(base_path):
    DataVars.BasePath = base_path
    if not os.path.exists(base_path):
        os.makedirs(base_path + DataVars.RGBPath)
        os.makedirs(base_path + DataVars.DepthPath)
        os.makedirs(base_path + DataVars.EXRDepthPath)