from cProfile import label
import os
import sys
from typing import Dict, List, Optional, Sequence, TextIO
import urllib.request

from sklearn.utils import shuffle

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")  # Report only TF errors by default

import numpy as np
import tensorflow as tf
DATASET_DIR = "fruits-360_dataset/fruits-360"

class FRUITS:
    H: int = 100
    W: int = 100
    C: int = 3
    LABELS: List[str] = os.listdir(DATASET_DIR+"/Test")
    def __init__(self) -> None:

        self.train = tf.keras.utils.image_dataset_from_directory(
            DATASET_DIR+"/Training",
            validation_split=0.2,
            subset="training",
            seed=4269,
            image_size=(FRUITS.H, FRUITS.W),
            batch_size = None)
        self.dev = tf.keras.utils.image_dataset_from_directory(
            DATASET_DIR+"/Training",
            validation_split=0.2,
            subset="validation",
            seed = 4269,
            shuffle = True,
            image_size=(FRUITS.H, FRUITS.W),
            batch_size = None
        )
        self.all = tf.keras.utils.image_dataset_from_directory(
            DATASET_DIR+"/Test",
            seed = 4269,
            shuffle = False,
            image_size=(FRUITS.H, FRUITS.W),
            batch_size = None
        ).shuffle(30000, reshuffle_each_iteration=False)
        