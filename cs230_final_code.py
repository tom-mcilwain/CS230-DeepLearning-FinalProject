# -*- coding: utf-8 -*-
"""cs230_final_code.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1XRZM2eD7aNMDp3mfhsIEgBSVq-paRelq
"""

import os
import cv2
from tqdm import tqdm
import numpy as np
import pandas as pd
import tensorflow as tf
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from keras.models import *
from keras.layers import *
from keras.optimizers import *
from tensorflow.keras import layers
from tensorflow.keras import regularizers
from tensorflow.keras.optimizers import *
from tensorflow.keras.layers import Conv2D, MaxPool2D, UpSampling2D, Dropout, concatenate
from tensorflow.keras.preprocessing.image import ImageDataGenerator, array_to_img, img_to_array, load_img
from sklearn.model_selection import train_test_split

IMAGE_SIZE = (224, 224)

"""# Training U-net using HAM10000 dataset

plotting performance
"""

# plotting performance of models
def plot_performance(hist, metric):

  EPOCHS = len(hist.history['loss'])

  plt.figure(figsize=(10,5))
  plt.subplot(1,2,1)
  plt.plot(range(EPOCHS), hist.history['loss'], label='Training')
  plt.plot(range(EPOCHS), hist.history['val_loss'], label='Validation')
  plt.title('Training and Validation Loss')
  plt.xlabel('Epoch')
  plt.ylabel('Loss')
  plt.legend()

  plt.subplot(1,2,2)
  plt.plot(range(EPOCHS), hist.history[metric], label='Training')
  plt.plot(range(EPOCHS), hist.history['val_' + metric], label='Validation')
  plt.title('Training and Validation ' + metric)
  plt.xlabel('Epoch')
  plt.ylabel(metric)
  plt.legend()

  print(f'Best Training {metric}:', np.around(np.amax(hist.history[metric]), 4))
  print(f'Best Validation {metric}:', np.around(np.amax(hist.history['val_' + metric]), 4))

images = np.load('/content/drive/MyDrive/HAM10000/new_images.npy')
masks = np.load('/content/drive/MyDrive/HAM10000/new_masks.npy')

##### Make train/dev/test set

train_images, val_images, train_masks, val_masks = train_test_split(images, masks, test_size=0.1)

print('Train images: ', train_images.shape)
print('Train masks: ', train_masks.shape)
print('Val images: ', val_images.shape)
print('Val masks: ', val_masks.shape)

# my coded one
class U_Net(tf.keras.Model):

    def __init__(self):
        super(U_Net, self).__init__()
        
        # Building the U-net model
        self.conv_1a = Conv2D(input_shape=(128,128,3), filters=32, kernel_size=(3, 3), strides=(1, 1), padding='same', activation='relu')
        self.conv_1b = Conv2D(filters=32, kernel_size=(3, 3), strides=(1, 1), padding='same', activation='relu')

        self.downstep_a = self.downstep(filters=64)
        self.downstep_b = self.downstep(filters=128)
        self.downstep_c = self.downstep(filters=256)
        self.downstep_d = self.downstep(filters=512)

        self.upsample = UpSampling2D(size=(2, 2))

        self.upstep_a = self.upstep(filters=64)
        self.upstep_b = self.upstep(filters=128)
        self.upstep_c = self.upstep(filters=256)

        self.conv_10a = Conv2D(filters=32, kernel_size=(3, 3), strides=(1, 1), padding='same', activation='relu')
        self.conv_10b = Conv2D(filters=32, kernel_size=(3, 3), strides=(1, 1), padding='same', activation='relu')
        self.conv_10c = Conv2D(filters=3, kernel_size=(1, 1), strides=(1, 1), padding='same', activation='relu')
        self.conv_10d = Conv2D(filters=1, kernel_size=(1, 1), strides=(1, 1), padding='same', activation='sigmoid')


    def downstep(self, filters):
      maxpool = MaxPool2D(pool_size=(2, 2), strides=(2,2))
      conv_1 = Conv2D(filters=filters, kernel_size=(3, 3), strides=(1, 1), padding='same', activation='relu')
      conv_2 = Conv2D(filters=filters, kernel_size=(3, 3), strides=(1, 1), padding='same', activation='relu')
      step = Sequential()
      step.add(maxpool)
      step.add(conv_1)
      step.add(conv_2)
      return step


    def upstep(self, filters):
      conv_1 = Conv2D(filters=filters, kernel_size=(3, 3), strides=(1, 1), padding='same', activation='relu')
      conv_2 = Conv2D(filters=filters, kernel_size=(3, 3), strides=(1, 1), padding='same', activation='relu')
      upsample = UpSampling2D(size=(2, 2))
      step = Sequential()
      step.add(conv_1)
      step.add(conv_2)
      step.add(upsample)
      return step


    def call(self, inputs):
        
        # Stepping down the U-net
        layer_1 = self.conv_1a(inputs)
        layer_1 = self.conv_1b(layer_1)
        layer_2 = self.downstep_a(layer_1)
        layer_3 = self.downstep_b(layer_2)
        layer_4 = self.downstep_c(layer_3)
        layer_5 = self.downstep_d(layer_4)
        
        # Stepping up the U-net
        layer_6 = self.upsample(layer_5)
        layer_7 = concatenate([layer_6, layer_4])
        layer_7 = self.upstep_a(layer_7)
        layer_8 = concatenate([layer_7, layer_3])
        layer_8 = self.upstep_b(layer_8)
        layer_9 = concatenate([layer_8, layer_2])
        layer_9 = self.upstep_c(layer_9)
        layer_10 = concatenate([layer_9, layer_1])
        layer_10 = self.conv_10a(layer_10)
        layer_10 = self.conv_10b(layer_10)
        layer_10 = self.conv_10c(layer_10)
        output = self.conv_10d(layer_10)
        
        return output
  

model = U_Net()
model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4), loss='binary_crossentropy', metrics=['accuracy'])

BATCH_SIZE = 64
EPOCHS = 20
hist = model.fit(train_images, train_masks, batch_size=BATCH_SIZE, epochs=EPOCHS, validation_data=(val_images, val_masks))

plot_performance(hist, metric='accuracy')

"""# Masking ISIC2020 data using trained U-net"""

images = np.load('/content/drive/MyDrive/ISIC2020/images.npy')
labels = np.load('/content/drive/MyDrive/ISIC2020/labels.npy')
metadata = np.load('/content/drive/MyDrive/ISIC2020/metas.npy')
masked_images = np.load('/content/drive/MyDrive/ISIC2020/masks.npy')

unet_model = tf.keras.models.load_model('/content/drive/MyDrive/ISIC2020/unet_model')

new_images = []
shape = (128, 128)
for image in images:
    new_images.append(cv2.resize(image, shape, interpolation=cv2.INTER_CUBIC))
new_images = np.stack(new_images)

masks = unet_model.predict(new_images, verbose=1)

new_masks = []
shape = (224, 224)
for mask in masks:
    new_masks.append(cv2.resize(mask, shape, interpolation=cv2.INTER_LANCZOS4))
masks = np.expand_dims(np.stack(new_masks), -1)
min, max = np.min(masks), np.max(masks)
masks = (masks-min) / (max-min)

masked_images = np.append(images, masks, axis=-1)
np.save('/content/drive/MyDrive/ISIC2020/masks.npy', masked_images)

num_print = 2

for i in range(num_print):
  ran = np.random.randint(0,images.shape[0])
  image = images[ran,:,:,:]
  masked = masked_images[ran,:,:,:]
  plt.figure(frameon=False)
  plt.subplot(1,2,1)
  plt.axis('off')
  plt.imshow(image)
  plt.subplot(1,2,2)
  plt.imshow(masked)
  plt.axis('off')

"""### Train test split"""

X = masked_images
X_meta = metadata
y = labels

test_size = 0.11

m = X.shape[0]

shuffle = np.random.permutation(m)
X = X[shuffle]
X_meta = X_meta[shuffle]
y = labels[shuffle]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, shuffle=False)
X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=test_size/(1-test_size), shuffle=False)
meta_split = np.split(X_meta, [int(m*(1-test_size*2)), int(m*(1-test_size)), m], axis=0)
X_train_meta = meta_split[0]
X_val_meta = meta_split[1]
X_test_meta = meta_split[2]

print('Training examples:', X_train.shape[0])
print('Validation examples:', X_val.shape[0])
print('Test examples:', X_test.shape[0])

"""# Building image classification models

# VGG model
"""

def fc_meta(input1):
  layer1 = Dense(512)(input1)
  layer1 = BatchNormalization()(layer1)
  layer1 = Activation('swish')(layer1)
  layer1 = Dropout(0.3)(layer1)
  layer1 = Dense(128)(layer1)
  layer1 = BatchNormalization()(layer1)
  layer1 = Activation('swish')(layer1)
  layer1 = Flatten()(layer1)
  return layer1

def vgg_block(layer, num_convolutions, num_filters):
  for i in range(num_convolutions):
    conv = Conv2D(filters=num_filters, kernel_size=(3, 3), strides=(1, 1), padding='same', activation='relu')
    layer = conv(layer)
  maxpool = MaxPool2D(pool_size=(2, 2), strides=(2,2))
  layer = maxpool(layer)
  return layer

def connect(layer0, layer1):
  layer = Concatenate()([layer0, layer1])
  output = Dense(64, activation='relu', kernel_regularizer='l2', kernel_initializer='HeNormal')(layer)
  layer = Dropout(0.5)(layer)
  output = Dense(1, activation='sigmoid')(layer)
  return output

def vgg_model():

  input0 = Input(shape=(224,224,4))  
  layer0 = vgg_block(input0, 2, 64)
  layer0 = vgg_block(layer0, 2, 128)
  layer0 = vgg_block(layer0, 2, 256)
  layer0 = vgg_block(layer0, 3, 512)
  layer0 = vgg_block(layer0, 3, 512)
  layer0 = Flatten()(layer0)
  layer0 = Dense(4096, activation='swish', kernel_regularizer='l2', kernel_initializer='HeNormal')(layer0)
  layer0 = Dropout(0.5)(layer0)

  input1 = Input(shape=(26))
  layer1 = fc_meta(input1)

  output = connect(layer0, layer1)

  model = Model(inputs=[input0, input1], outputs=output, name='vgg_model')

  return model


model_1 = vgg_model()
model_1.compile(optimizer=Adam(lr=1e-5), loss='binary_crossentropy', metrics=['accuracy', 'AUC'])

BATCH_SIZE = 64
EPOCHS = 150
hist_vgg = model_1.fit([X_train, X_train_meta], y_train, batch_size=BATCH_SIZE, epochs=EPOCHS, validation_data=([X_val, X_val_meta], y_val))

plot_performance(hist_vgg, 'auc')

model_1.evaluate([X_test, X_test_meta], y_test, verbose=1)

model_1.save('/content/drive/MyDrive/ISIC2020/vgg_model')

"""# Siamese approach"""

def siamese():

  input0 = Input(shape=(224,224,4))
  input0a = Add()([input0, input0]) / 2 # copying input
  input0b = Add()([input0, input0]) / 2 # copying input

  layer0a = vgg_block(input0a, 2, 64)
  saved = layer0a
  layer0b = vgg_block(input0b, 2, 64)

  layer0 = Concatenate()([layer0a, layer0b])
  layer0 = vgg_block(layer0, 3, 128)

  saved = tf.tile(saved, (1,1,1,2))
  saved = MaxPool2D()(saved)
  layer0 = Add()([layer0, saved])

  layer0a = vgg_block(layer0, 2, 32)
  layer0b = vgg_block(layer0, 2, 32)

  layer0 = Concatenate()([layer0a, layer0b])
  layer0 = Dense(256, kernel_regularizer='l2', kernel_initializer='HeNormal')(layer0)
  layer0 = BatchNormalization(axis=-1)(layer0)
  layer0 = Activation('relu')(layer0)
  layer0 = Dropout(0.5)(layer0)
  layer0 = Flatten()(layer0)

  # metadata
  input1 = Input(shape=(26))
  layer1 = fc_meta(input1)

  output = connect(layer0, layer1)

  model = Model(inputs=[input0, input1], outputs=output, name='Siamese')

  return model

model_2 = siamese()
model_2.compile(optimizer=Adam(learning_rate=1e-5), loss='binary_crossentropy', metrics=['accuracy', 'AUC'])

BATCH_SIZE = 64
EPOCHS = 150
hist_siamese = model_2.fit([X_train, X_train_meta], y_train, batch_size=BATCH_SIZE, epochs=EPOCHS, validation_data=([X_val, X_val_meta], y_val))

plot_performance(hist_siamese, metric='auc')

model_2.evaluate([X_test, X_test_meta], y_test, verbose=2)

model_2.save('/content/drive/MyDrive/ISIC2020/siamese_model')

"""# Transfer learning"""

# Using existing models
def transfer(base_model):

  base_model.trainable = True

  input0 = base_model.input
  layer0 = base_model.output
  layer0 = vgg_block(layer0, 1, 64)
  layer0 = Flatten()(layer0)
  layer0 = Dropout(0.5)(layer0)

  input1 = Input(shape=(26))
  layer1 = fc_meta(input1)

  output = connect(layer0, layer1)

  model = Model(inputs=[input0, input1], outputs=output)
  
  return model

X_t = X_train[:,:,:,:-1] * np.expand_dims(X_train[:,:,:,-1], -1)
X_v = X_val[:,:,:,:-1] * np.expand_dims(X_val[:,:,:,-1], -1)
X_te = X_test[:,:,:,:-1] * np.expand_dims(X_test[:,:,:,-1], -1)

efficientnet = tf.keras.applications.EfficientNetB0(input_shape=(224,224,3), include_top=False, weights='imagenet')
model_3 = transfer(efficientnet)
model_3.compile(optimizer=Adam(lr=1e-5), loss='binary_crossentropy', metrics=['accuracy', 'AUC'])

BATCH_SIZE = 64
EPOCHS = 150
hist_transfer = model_3.fit([X_t, X_train_meta], y_train, batch_size=BATCH_SIZE, epochs=EPOCHS, validation_data=([X_v, X_val_meta], y_val))

plot_performance(hist_transfer, 'auc')

model_3.evaluate([X_te, X_test_meta], y_test)