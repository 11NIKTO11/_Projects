import pydicom
from matplotlib import pyplot as plt
from glob import glob

from cProfile import label
import os
import sys
from typing import Dict, List, Optional, Sequence, TextIO
import urllib.request

from sklearn.utils import shuffle

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")  # Report only TF errors by default

import numpy as np
import tensorflow as tf
DATASET_DIR = "flowers"
test_files = glob('./body_parts/test/test/test/*/*/*/*')

class BODY_PARTS:
    H: int = 224
    W: int = 224
    C: int = 3
    LABELS: List[str] = ['Abdomen', 'Ankle', 'Cervical Spine',
       'Chest', 'Clavicles', 'Elbow', 'Feet', 'Finger', 'Forearm', 'Hand',
       'Hip', 'Knee', 'Lower Leg', 'Lumbar Spine', 'Others', 'Pelvis',
       'Shoulder', 'Sinus', 'Skull', 'Thigh', 'Thoracic Spine', 'Wrist']
    
    def __init__(self) -> None:
        X = []
        for _file in test_files[:5]:
            img = pydicom.dcmread(_file).pixel_array
            if len(img.shape) > 2:
                for i in range(0, len(img.shape[0])):
                    img =  img[i, : , :]
                    img = img / img.max() - 0.5

                    img = img.astype(np.float32)
                    X.append(img)

                    break
            else:
                img = img.astype(np.float32)
                X.append(img)
        self.train = X 

        
bp = BODY_PARTS()
for img in bp.train[:5]:
    plt.imshow(img, cmap = 'gray')
    plt.show()