from cProfile import label
import os
import sys
from typing import Dict, List, Optional, Sequence, TextIO
import urllib.request
from sklearn.utils import shuffle

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")  # Report only TF errors by default

import numpy as np
import tensorflow as tf
DATASET_DIR = "alzheimer"

class ALZHEIMER:
    H: int = 224
    W: int = 224
    C: int = 1
    LABELS: List[str] = [
        # demented
        "Mild_Demented", "Moderate_Demented", "Non_Demented", "Very_Mild_Demented"     
    ]
    def __init__(self) -> None:

        self.train = tf.keras.utils.image_dataset_from_directory(
            DATASET_DIR,
            validation_split=0.2,
            subset="training",
            seed=4269,
            image_size=(ALZHEIMER.H, ALZHEIMER.W),
            batch_size = None)
        self.dev = tf.keras.utils.image_dataset_from_directory(
            DATASET_DIR,
            validation_split=0.2,
            subset="validation",
            seed = 4269,
            shuffle = True,
            image_size=(ALZHEIMER.H, ALZHEIMER.W),
            batch_size = None
        )
        self.all = tf.keras.utils.image_dataset_from_directory(
            DATASET_DIR,
            seed = 4269,
            shuffle = False,
            image_size=(ALZHEIMER.H, ALZHEIMER.W),
            batch_size = None
        ).shuffle(5000, reshuffle_each_iteration=False)

        