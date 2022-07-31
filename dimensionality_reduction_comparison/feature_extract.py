#!/usr/bin/env python3
import argparse
from audioop import avg
import datetime
import os
import re
from typing import Dict, Tuple

from sklearn import metrics
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")  # Report only TF errors by default

import numpy as np
import tensorflow as tf

import flowers_dataset as fd
import alzheimer_dataset as ad
import fruits_dataset as od
import efficient_net
import efficientnet.tfkeras as efn 
import pandas as pd

# TODO: Define reasonable defaults and optionally more parameters
parser = argparse.ArgumentParser()
parser.add_argument("--batch_size", default=30, type=int, help="Batch size.")
parser.add_argument("--epochs", default=7, type=int, help="Number of epochs.")
parser.add_argument("--seed", default=42, type=int, help="Random seed.")
parser.add_argument("--threads", default=0, type=int, help="Maximum number of threads to use.")
parser.add_argument("--l2", default = 0.001, type=float)
parser.add_argument("--dropout", default =  0.3, type = float)
parser.add_argument("--label_smoothing", default=0.2, type=float, help="Label smoothing.")
DATASET = ad.ALZHEIMER
IDF = "B0-ut"
DATA = "alzheimer"
SAVE_PREDICTIONS=True
#TODO add confusion matrix
class Model(tf.keras.Model):
    def __init__(self, args: argparse.Namespace, train):
        
        # efficientnet_b0 = efficient_net.pretrained_efficientnet_b0(include_top=False)
        # eff_output = efficientnet_b0.output[0]
        # efficientnet_b0 = tf.keras.applications.EfficientNetV2M(
        #     include_top=False,
        #     weights="imagenet",
        #     input_tensor=None,
        #     input_shape=None,
        #     pooling="avg",
        #     classes=1000,
        #     classifier_activation="softmax"
        # )
        efficientnet_b0 = efn.EfficientNetB0(
            include_top=False,
            weights='noisy-student',
            pooling="avg")
        eff_output =efficientnet_b0.output
        
        input = efficientnet_b0.input
        output = tf.keras.layers.Dropout(args.dropout)(eff_output)
        output = tf.keras.layers.Dense(len(DATASET.LABELS), activation = tf.nn.softmax, kernel_regularizer = tf.keras.regularizers.l2(args.l2))(output)
        
        super().__init__(inputs = input, outputs = {"output" : output, "features": eff_output})
        self.efficientnet_b0 = efficientnet_b0
        #tf.keras.optimizers.schedules.CosineDecay(0.0001, args.epochs*train.cardinality().numpy()/args.batch_size)
        self.compile(
            optimizer = tf.optimizers.Adam(learning_rate = 0.0001),
            loss = {"output" : tf.losses.CategoricalCrossentropy(label_smoothing = args.label_smoothing),
            },
            metrics = {"output" : [ tf.metrics.CategoricalAccuracy(name = "accuracy")]}
        )
        self.tb_callback = tf.keras.callbacks.TensorBoard(args.logdir)

    def predict_step(self, data):
        y_pred = self(data, training=False)
        return (y_pred["features"], y_pred["output"])
def main(args: argparse.Namespace) -> None:
    # Fix random seeds and threads
    tf.keras.utils.set_random_seed(args.seed)
    tf.config.threading.set_inter_op_parallelism_threads(args.threads)
    tf.config.threading.set_intra_op_parallelism_threads(args.threads)

    # Create logdir name
    args.logdir = os.path.join("logs", "{}-{}-{}".format(
        os.path.basename(globals().get("__file__", "notebook")),
        datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S"),
        ",".join(("{}={}".format(re.sub("(.)[^_]*_?", r"\1", k), v) for k, v in sorted(vars(args).items())))
    ))

    # Load the data
    flowers = DATASET()
    generator = tf.random.Generator.from_seed(args.seed)
    def train_augment(image: tf.Tensor, label: tf.Tensor) -> Tuple[tf.Tensor, tf.Tensor]:
        
        if generator.uniform([]) >= 0.5:
            image = tf.image.flip_left_right(image)
        image = tf.image.resize_with_crop_or_pad(image, DATASET.H + 100, DATASET.W + 100)
        image = tf.image.resize(image, [generator.uniform([], DATASET.H, DATASET.H + 100 + 1, dtype=tf.int32),
                                        generator.uniform([], DATASET.W, DATASET.H + 100 + 1, dtype=tf.int32)])
        image = tf.image.crop_to_bounding_box(
            image, target_height=DATASET.H, target_width=DATASET.W,
            offset_height=generator.uniform([], maxval=tf.shape(image)[0] - DATASET.H + 1, dtype=tf.int32),
            offset_width=generator.uniform([], maxval=tf.shape(image)[1] - DATASET.W + 1, dtype=tf.int32),
        )
        return image, label    
    train_dataset = (flowers.train
        .shuffle(10000, seed = args.seed)
        .map(lambda image, label : train_augment(image, {"output": tf.one_hot(label, len(DATASET.LABELS))}))
        .batch(args.batch_size)
        .prefetch(tf.data.AUTOTUNE))
    dev_dataset = (flowers.dev
        .map(lambda image, label : (image, {"output": tf.one_hot(label, len(DATASET.LABELS))}))
        .batch(args.batch_size)
        .prefetch(tf.data.AUTOTUNE))
    #dirty, but the dev is shuffled automatically on each pass (otherwise single class data),
    # so we need to do split in a different dataset that is shuffled only once


    test_images = (flowers.all
        .take(10000)
        .map(lambda im, label : im)
        .batch(1)
        )
    test_labels = (flowers.all
        .take(10000)
        .map(lambda im, label : label)
        .batch(1)
        )
    #test_labels = np.array(labels)

    model = Model(args, train= train_dataset)
    model.fit(
        train_dataset, epochs = args.epochs, shuffle=True,
        validation_data = dev_dataset, callbacks = [model.tb_callback]
    )
    #TODO find why dev is shuffled, possibly use dev_dataset
    feature_vectors, outputs  = model.predict(test_images)
    predictions = tf.argmax(outputs, axis = 1)
    #err = tf.reduce_sum(tf.where(predictions != np.array(list(test_labels.as_numpy_iterator()), dtype = np.int32).ravel(), 1, 0))/outputs.shape[0]
    #print(err)
    #print(predictions)
    #print(feature_vectors.shape)
    np.save("dev_"+DATA+"_feature_vectors"+IDF, feature_vectors)
    np.save("dev_"+DATA+"_classes"+IDF, np.array(list(test_labels.as_numpy_iterator()), dtype = np.int32).ravel())
    if SAVE_PREDICTIONS:
        np.save("dev_"+DATA+"_predictions"+IDF,outputs)
    # Generate test set annotations, but in `args.logdir` to allow parallel execution.
    


if __name__ == "__main__":
    args = parser.parse_args([] if "__file__" not in globals() else None)
    main(args)
