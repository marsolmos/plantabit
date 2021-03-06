'''Preprocessing and training pipelines for Planta-Bit'''
import datetime
import json
import os
import pickle
import yaml
import zipfile
import matplotlib.pyplot as plt

# Don't display general information messages from tf-gpu
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import tensorflow as tf
from tensorflow.keras import layers
from tensorflow.keras import metrics
from tensorflow.keras import applications
from tensorflow.keras.optimizers import SGD
from tensorflow.keras.regularizers import l2
from tensorflow.keras.models import Sequential
from tensorflow.keras.callbacks import TensorBoard
from tensorflow.keras.preprocessing.image import ImageDataGenerator


# Read parameters and assign them to a local variable
params = yaml.safe_load(open("params.yaml"))["train"]
seed = params["seed"]
model_name = params["model_name"]
dataset = params["dataset"]
epochs = params["epochs"]
steps_per_epoch = params["steps_per_epoch"]
batch = params["batch"]
loss = params["loss"]
learning_rate = params["learning_rate"]
l2_reg = params["l2_reg"]
momentum = params["momentum"]

# Define paths
base_dir = os.path.join("D:/Data Warehouse/plantabit", dataset)
train_dir = os.path.join(base_dir, 'train')
validation_dir = os.path.join(base_dir, 'validation')
train_scores = "utils/classifier/dvc_objects/train_scores.json"
val_scores = "utils/classifier/dvc_objects/val_scores.json"

# Define GPU usage for training
physical_devices = tf.config.experimental.list_physical_devices('GPU')
tf.config.experimental.set_memory_growth(physical_devices[0],True)

# Initialize TensorBoard
model_log_name = model_name + "-" + dataset + "-" + datetime.datetime.now().strftime("%Y%m%d/%H%M%S")
log_dir = "utils/classifier/models/logs/" + model_log_name
tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=log_dir, histogram_freq=1)
tensorboard = TensorBoard(
    log_dir='logs', histogram_freq=0, write_graph=True, write_images=True,
    update_freq='epochs', profile_batch=2, embeddings_freq=0,
    embeddings_metadata=None
)

# Adding rescale, rotation_range, width_shift_range, height_shift_range,
# shear_range, and zoom_range to our ImageDataGenerator
train_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=40,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.2,
    zoom_range=0.2,
    )

# Note that the validation data should not be augmented!
val_datagen = ImageDataGenerator(rescale=1./255)

# Flow training images in batches of 32 using train_datagen generator
train_generator = train_datagen.flow_from_directory(
        train_dir,  # This is the source directory for training images
        target_size=(150, 150),  # All images will be resized to 150x150
        batch_size=batch,
        seed=seed,
        class_mode='categorical')


# Flow validation images in batches of 32 using val_datagen generator
validation_generator = val_datagen.flow_from_directory(
        validation_dir,
        target_size=(150, 150),
        batch_size=batch,
        seed=seed,
        class_mode='categorical')

# Build the VGG16 network
base_model = applications.VGG16(weights='imagenet', include_top=False, input_shape=(150,150,3))
base_model.trainable = False # Not trainable weights
print('Base model loaded')

# Build a classifier model to put on top of the convolutional model
model = Sequential()
model.add(base_model)
model.add(layers.Flatten())
model.add(layers.Dense(256, activation='relu'))
model.add(layers.Dropout(0.5))
# Create output layer with a 12 units and softmax activation
model.add(layers.Dense(
                    12, activation='softmax',
                    kernel_regularizer=l2(l2_reg), bias_regularizer=l2(l2_reg)
                    ))


# Configure and compile the model
model.compile(loss=loss,
              optimizer=SGD(
                            learning_rate=learning_rate,
                            momentum=momentum
                            ),
              metrics=[
                    metrics.CategoricalAccuracy(),
                    metrics.AUC(),
              ])

# Display model summary
model.summary()

# Train model to train-validation data
history = model.fit(
      train_generator,
      steps_per_epoch=steps_per_epoch,
      epochs=epochs,
      validation_data=validation_generator,
      validation_steps=1,
      verbose=1,
      callbacks=[tensorboard_callback]
      )

# Save the model to disk into historical archive folder
print('\nSaving model into historical registry as {}'.format(model_name))
save_name = 'utils/classifier/models/{}'.format(model_name)
model.save(save_name)

# Save model to disk for DVC - MLOps tracking
print('Saving model for DVC - MLOps tracking\n')
save_name = 'utils/classifier/dvc_objects/model'
model.save(save_name)

# Save metrics to disk for DVC - MLOps tracking
train_loss = history.history['loss'][-1]
train_acc = history.history['categorical_accuracy'][-1]
val_loss = history.history['val_loss'][-1]
val_acc = history.history['val_categorical_accuracy'][-1]
with open(train_scores, "w") as fd:
    json.dump({"train_loss": train_loss, "train_acc": train_acc}, fd, indent=4)
with open(val_scores, "w") as fd:
    json.dump({"val_loss": val_loss, "val_acc": val_acc}, fd, indent=4)
