import os

import json
from json import JSONEncoder

import numpy as np

import datavars as datavars

class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)

def writeJSON(count):
    npData = {"points_2d": np.array(datavars.points_2d)}
    encodedNPData = json.dumps(npData, cls=NumpyArrayEncoder)

    print("writing file ..")
    file = 'contour-%d.json'
    path = os.path.join(os.getcwd(), (file % count))
    with open(path, "w") as outfile:
        outfile.write(encodedNPData)