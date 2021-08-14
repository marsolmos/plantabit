'''Preprocessing and training pipelines for Planta-Bit'''
import os
import pickle
import yaml
import zipfile
import matplotlib.pyplot as plt

# Don't display general information messages from tf-gpu
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import tensorflow as tf
from tensorflow.keras import layers
from tensorflow.keras import Model
from tensorflow.keras.optimizers import RMSprop
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

# Define paths
base_dir = os.path.join("D:/Data Warehouse/plantabit", dataset)
train_dir = os.path.join(base_dir, 'train')
validation_dir = os.path.join(base_dir, 'validation')

# Define GPU usage for training
physical_devices = tf.config.experimental.list_physical_devices('GPU')
tf.config.experimental.set_memory_growth(physical_devices[0],True)

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

# Our input feature map is 150x150x3: 150x150 for the image pixels, and 3 for
# the three color channels: R, G, and B
img_input = layers.Input(shape=(150, 150, 3))

# First convolution extracts 16 filters that are 3x3
# Convolution is followed by max-pooling layer with a 2x2 window
x = layers.Conv2D(16, 3, activation='relu')(img_input)
x = layers.MaxPooling2D(2)(x)

# Second convolution extracts 32 filters that are 3x3
# Convolution is followed by max-pooling layer with a 2x2 window
x = layers.Conv2D(32, 3, activation='relu')(x)
x = layers.MaxPooling2D(2)(x)

# Third convolution extracts 64 filters that are 3x3
# Convolution is followed by max-pooling layer with a 2x2 window
x = layers.Convolution2D(64, 3, activation='relu')(x)
x = layers.MaxPooling2D(2)(x)

# Flatten feature map to a 1-dim tensor
x = layers.Flatten()(x)

# Create a fully connected layer with ReLU activation and 512 hidden units
x = layers.Dense(512, activation='relu')(x)

# Add a dropout rate of 0.5
x = layers.Dropout(0.5)(x)

# Create output layer with a single node and sigmoid activation
output = layers.Dense(12, activation='softmax')(x)

# Configure and compile the model
model = Model(img_input, output)
model.compile(loss=loss,
              optimizer=RMSprop(learning_rate=learning_rate),
              metrics=['categorical_accuracy'])

history = model.fit(
      train_generator,
      steps_per_epoch=steps_per_epoch,
      epochs=epochs,
      validation_data=validation_generator,
      validation_steps=50,
      verbose=1)

# Save the model to disk into historical archive folder
print('\nSaving model into historical registry as {}'.format(model_name))
save_name = 'utils/classifier/models/{}'.format(model_name)
model.save(save_name)

# Save the model and metrics to disk into historical archive folder
print('Saving model for DVC - MLOps tracking\n')
save_name = 'utils/classifier/dvc_objects/model'
model.save(save_name)
