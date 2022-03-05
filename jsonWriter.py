import os

import json
from json import JSONEncoder

import numpy as np

import DataVars as DataVars

class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)

def writeJSON(count):
    npData = {"points_2d": np.array(DataVars.points_2d), "ground_truth": np.array(DataVars.groundTruth), "camera_matrix": np.array(DataVars.cameraMatrix)}

    encodedNPData = json.dumps(npData, cls=NumpyArrayEncoder)

    print("writing file ..")
    file = 'contour-%d.json'
    path = os.path.join(os.getcwd()+ '//exported-data//', (file % count))
    with open(path, "w") as outfile:
        outfile.write(encodedNPData)