#!/usr/bin/env python
# -*- coding: utf-8 -*-



# Imports
from __future__ import print_function
from keras.models import Sequential
from keras.layers import Dense, Activation,Dropout,TimeDistributed
from keras.layers import LSTM,SimpleRNN
from keras.optimizers import RMSprop
from keras.utils.data_utils import get_file
import numpy as np
import random
import sys
import os, os.path
from os import listdir
from os.path import isfile, join
from unicodedata import normalize
import re
import argparse


#argparse file path
parser = argparse.ArgumentParser(description='Image Captionning.')
parser.add_argument('seed', type=str, help='string to init LSTM.')
parser.add_argument('number_of_letters', type=int, help='string to init LSTM.')
args = parser.parse_args()
seed_=args.seed
nb_letters=args.number_of_letters

#directories where files are
out_path="../02-train_LSTM/english/data/"
last_checkpoint_dir="../02-train_LSTM/english/data/weights/weight_attempt_s02/"
all_files = [f for f in listdir(last_checkpoint_dir) if isfile(join(last_checkpoint_dir, f))]
if len(all_files)!=1:
    print("Something wrong with model checkpoint, please verify concerned directory")

last_checkpoint = last_checkpoint_dir+all_files[0]
#print("Using checkpoint : %s" %last_checkpoint)

#getting files from learning session
file_name=out_path+'input/english.txt'
text = open(file_name).read()
text=normalize('NFKD',text.decode('latin1')).encode('ASCII', 'ignore')
text = re.sub("\n\n+" , "\n", text)

#setting variables
chars = sorted(list(set(text)))
VOCAB_SIZE = len(chars)
    #creating mapping between indexes and characters
char_indices = dict((c, i) for i, c in enumerate(chars))
indices_char = dict((i, c) for i, c in enumerate(chars))


#setting keras model
HIDDEN_DIM= 500 #500
LAYER_NUM = 2


model = Sequential()
model.add(LSTM(HIDDEN_DIM, input_shape=(None, VOCAB_SIZE), return_sequences=True))
for i in range(LAYER_NUM - 1):
    model.add(LSTM(HIDDEN_DIM, return_sequences=True))
model.add(TimeDistributed(Dense(VOCAB_SIZE)))
model.add(Activation('softmax'))
model.compile(loss="categorical_crossentropy", optimizer="rmsprop")

#loading learned parameters
model.load_weights(last_checkpoint)


#seed with particular text:
def generate_text_seeded(model,seed,length, vocab_size, ix_to_char):
    # starting with random character
    # char_indices
    ix = [char_indices[x] for x in seed]
    y_char = [x for x in seed]
    X = np.zeros((1, length, vocab_size))
    for i in range(len(ix)) :
        X[0, i, :][ix[i]] = 1
        print(ix_to_char[ix[i]], end="")
    to_substract = len(ix)
    for i in range(length-to_substract):
        # appending the last predicted character to sequence
        X[0, i, :][ix[-1]] = 1
        print(ix_to_char[ix[-1]], end="")
        ix = np.argmax(model.predict(X[:, :i+1, :])[0], 1)
        y_char.append(ix_to_char[ix[-1]])
    return ('').join(y_char)



if __name__ == "__main__":
    generate_text_seeded(model,normalize('NFKD',seed_.decode('latin1')), nb_letters, VOCAB_SIZE, indices_char) #700
