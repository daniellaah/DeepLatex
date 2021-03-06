# small train
from os import listdir
import numpy as np
from numpy import array
from numpy import argmax
from pandas import DataFrame
from nltk.translate.bleu_score import corpus_bleu
from pickle import load

from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras.utils import to_categorical
from keras.preprocessing.image import load_img
from keras.preprocessing.image import img_to_array
from keras.applications.vgg16 import preprocess_input
from keras.applications.vgg16 import VGG16
from keras.utils import plot_model
from keras.models import Model
from keras.layers import Input
from keras.layers import Dense
from keras.layers import Flatten
from keras.layers import LSTM
from keras.layers import RepeatVector
from keras.layers import TimeDistributed
from keras.layers import Embedding
from keras.layers.merge import concatenate
from keras.layers.pooling import GlobalMaxPooling2D

import code

def load_name_to_latex(filter_file, formula_file):
    name_to_latex = dict()
    f_file = open(formula_file, 'r')
    formulas = f_file.readlines()
    with open(filter_file, 'r') as f:
        for line in f.readlines():
            name = line.strip().split('.')
            index = line.strip().split(' ')
            latex = formulas[index].strip()
            name_to_latex[name] = 'SOL' + latex + 'EOL'
    return name_to_latex

def create_train_data(name_to_latex):
    for name, latex in name_to_latex.items():
        y
        
# load doc into memory
def load_doc(filename):
	# open the file as read only
	file = open(filename, 'r')
	# read all text
	text = file.read()
	# close the file
	file.close()
	return text

# load a pre-defined list of photo identifiers
def load_set(filename):
	doc = load_doc(filename)
	dataset = list()
	# process line by line
	for line in doc.split('\n'):
		# skip empty lines
		if len(line) < 1:
			continue
		# get the image identifier
		identifier = line.split('.')[0]
		dataset.append(identifier)
	return set(dataset)

# split a dataset into train/test elements
def train_test_split(dataset, train_size, test_size):
    # order keys so the split is consistent
    ordered = sorted(dataset)
    if train_size + test_size > len(ordered):
        print('train_size + test_size exceed the size of dataset')
        train_size = len(ordered) * 0.7
        test_size = len(ordered) - train_size
        print('use default split, train_size: {}, test_size: {}'
                .format(len(train_size), len(test_size)))
    # return split dataset as two new sets
    return set(ordered[:train_size]), set(ordered[train_size:train_size+test_size])

# load clean descriptions into memory
def load_clean_descriptions(filename, dataset):
	# load document
	doc = load_doc(filename)
	descriptions = dict()
	for line in doc.split('\n'):
		# split line by white space
		tokens = line.split()
		# split id from description
		image_id, image_desc = tokens[0], tokens[1:]
		# skip images not in the set
		if image_id in dataset:
			# store
			descriptions[image_id] = 'startseq ' + ' '.join(image_desc) + ' endseq'
	return descriptions

# load photo features
def load_photo_features(filename, dataset):
	# load all features
	all_features = load(open(filename, 'rb'))
	# filter features
	features = {k: all_features[k] for k in dataset}
	return features

# fit a tokenizer given caption descriptions
def create_tokenizer(descriptions):
	lines = list(descriptions.values())
	tokenizer = Tokenizer()
	tokenizer.fit_on_texts(lines)
	return tokenizer

# create sequences of images, input sequences and output words for an image
def create_sequences(tokenizer, desc, image, max_length):
	Ximages, XSeq, y = list(), list(),list()
	vocab_size = len(tokenizer.word_index) + 1
	# integer encode the description
	seq = tokenizer.texts_to_sequences([desc])[0]
	# split one sequence into multiple X,y pairs
	for i in range(1, len(seq)):
		# select
		in_seq, out_seq = seq[:i], seq[i]
		# pad input sequence
		in_seq = pad_sequences([in_seq], maxlen=max_length)[0]
		# encode output sequence
		out_seq = to_categorical([out_seq], num_classes=vocab_size)[0]
		# store
		Ximages.append(image)
		XSeq.append(in_seq)
		y.append(out_seq)
	# Ximages, XSeq, y = array(Ximages), array(XSeq), array(y)
	return [Ximages, XSeq, y]

def read_glove_vecs(glove_file):
    with open(glove_file, 'r') as f:
        words = set()
        word_to_vec = {}
        for line in f:
            line = line.strip().split()
            curr_word = line[0]
            words.add(curr_word)
            word_to_vec[curr_word] = np.array(line[1:], dtype=np.float64)
    return word_to_vec

def pretrained_embedding_layer(tokenizer, vocab_size, max_length, word_to_vec):
	dimension = word_to_vec['a'].shape[0]
	weights = np.zeros((vocab_size, dimension))
	for word, index in tokenizer.word_index.items():
		if word in word_to_vec:
			weights[index, :] = word_to_vec[word]
	embedding_layer = Embedding(vocab_size, dimension, 
                                weights=[weights], input_length=max_length, 
                                mask_zero=True, trainable=True)
	return embedding_layer

# define the captioning model
def define_model(vocab_size, max_length, word_to_vec):
	# feature extractor (encoder)
	inputs1 = Input(shape=(7, 7, 512))
	fe1 = GlobalMaxPooling2D()(inputs1)
	fe2 = Dense(128, activation='relu')(fe1)
	fe3 = RepeatVector(max_length)(fe2)
	# embedding
	inputs2 = Input(shape=(max_length,))
	emb2 = pretrained_embedding_layer(tokenizer, vocab_size, max_length, word_to_vec)(inputs2)
	emb3 = LSTM(256, return_sequences=True)(emb2)
	emb4 = TimeDistributed(Dense(128, activation='relu'))(emb3)
	# merge inputs
	merged = concatenate([fe3, emb4])
	# language model (decoder)
	lm2 = LSTM(500)(merged)
	lm3 = Dense(500, activation='relu')(lm2)
	outputs = Dense(vocab_size, activation='softmax')(lm3)
	# tie it together [image, seq] [word]
	model = Model(inputs=[inputs1, inputs2], outputs=outputs)
	model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
	print(model.summary())
	# plot_model(model, show_shapes=True, to_file='plot.png')
	return model

# data generator, intended to be used in a call to model.fit_generator()
def data_generator(descriptions, features, tokenizer, max_length, n_step):
	# loop until we finish training
	while 1:
		# loop over photo identifiers in the dataset
		keys = list(descriptions.keys())
		for i in range(0, len(keys), n_step):
			Ximages, XSeq, y = list(), list(),list()
			for j in range(i, min(len(keys), i+n_step)):
				image_id = keys[j]
				# retrieve photo feature input
				image = features[image_id][0]
				# retrieve text input
				desc = descriptions[image_id]
				# generate input-output pairs
				in_img, in_seq, out_word = create_sequences(tokenizer, desc, image, max_length)
				for k in range(len(in_img)):
					Ximages.append(in_img[k])
					XSeq.append(in_seq[k])
					y.append(out_word[k])
			# yield this batch of samples to the model
			yield [[array(Ximages), array(XSeq)], array(y)]

            
# data generator, intended to be used in a call to model.fit_generator()
def create_data(descriptions, features, tokenizer, max_length):
	# loop over photo identifiers in the dataset
	keys = list(descriptions.keys())
	Ximages, XSeq, y = list(), list(),list()
	for i in range(0, len(keys)):
		image_id = keys[i]
		# retrieve photo feature input
		image = features[image_id][0]
		# retrieve text input
		desc = descriptions[image_id]
		# generate input-output pairs
		in_img, in_seq, out_word = create_sequences(tokenizer, desc, image, max_length)
		for k in range(len(in_img)):
			Ximages.append(in_img[k])
			XSeq.append(in_seq[k])
			y.append(out_word[k])
		# yield this batch of samples to the model
	return [[array(Ximages), array(XSeq)], array(y)]
            
            
# map an integer to a word
def word_for_id(integer, tokenizer):
	for word, index in tokenizer.word_index.items():
		if index == integer:
			return word
	return None

# generate a description for an image
def generate_desc(model, tokenizer, photo, max_length):
	# seed the generation process
	in_text = 'startseq'
	# iterate over the whole length of the sequence
	for i in range(max_length):
		# integer encode input sequence
		sequence = tokenizer.texts_to_sequences([in_text])[0]
		# pad input
		sequence = pad_sequences([sequence], maxlen=max_length)
		# predict next word
		yhat = model.predict([photo,sequence], verbose=0)
		# convert probability to integer
		yhat = argmax(yhat)
		# map integer to word
		word = word_for_id(yhat, tokenizer)
		# stop if we cannot map the word
		if word is None:
			break
		# append as input for generating the next word
		in_text += ' ' + word
		# stop if we predict the end of the sequence
		if word == 'endseq':
			break
	return in_text

# evaluate the skill of the model
def evaluate_model(model, descriptions, photos, tokenizer, max_length, display=False):
	actual, predicted = list(), list()
	# step over the whole set
	for key, desc in descriptions.items():
		# generate description
		yhat = generate_desc(model, tokenizer, photos[key], max_length)
		# store actual and predicted
		actual.append([desc.split()])
		predicted.append(yhat.split())
		if display:
			print('Actual:    %s' % desc)
			print('Predicted: %s' % yhat)
	# calculate BLEU score
	bleu = corpus_bleu(actual, predicted)
	return bleu

# # load dev set
# filename = 'Flickr8k_text/Flickr_8k.devImages.txt'
# dataset = load_set(filename)
# print('Dataset: %d' % len(dataset))
# # train-test split
# train, test = train_test_split(dataset, 100, 100)
# print('Train=%d, Test=%d' % (len(train), len(test)))
dev_dataset = load_set('Flickr8k_text/Flickr_8k.devImages.txt')
train_dataset = load_set('Flickr8k_text/Flickr_8k.trainImages.txt')
train, _ = train_test_split(train_dataset, 1000, 100)
test, _ = train_test_split(dev_dataset, 100, 100)
print('Train=%d, Test=%d' % (len(train), len(test)))
# descriptions
train_descriptions = load_clean_descriptions('descriptions.txt', train)
test_descriptions = load_clean_descriptions('descriptions.txt', test)
print('Descriptions: train=%d, test=%d' % (len(train_descriptions), len(test_descriptions)))
# photo features
train_features = load_photo_features('features.pkl', train)
test_features = load_photo_features('features.pkl', test)
print('Photos: train=%d, test=%d' % (len(train_features), len(test_features)))
# prepare tokenizer
tokenizer = create_tokenizer(train_descriptions)
vocab_size = len(tokenizer.word_index) + 1
print('Vocabulary Size: %d' % vocab_size)
# determine the maximum sequence length
max_length = max(len(s.split()) for s in list(train_descriptions.values()))
print('Description Length: %d' % max_length)

train_data = create_data(train_descriptions, train_features, tokenizer, max_length)
# code.interact(local=locals())

# define experiment
model_name = 'baseline1'
verbose = 1
n_epochs = 100
n_photos_per_update = 2
n_batches_per_epoch = int(len(train) / n_photos_per_update)
n_repeats = 1

# run experiment
train_results, test_results = list(), list()
word_to_vec = read_glove_vecs('glove.6B/glove.6B.100d.txt')

for i in range(n_repeats):
	# define the model
	model = define_model(vocab_size, max_length, word_to_vec)
	# fit model
# 	model.fit_generator(data_generator(train_descriptions,
#                                     train_features,
#                                     tokenizer,
#                                     max_length,
#                                     n_photos_per_update),
#                  steps_per_epoch=n_batches_per_epoch,
#                  epochs=n_epochs, verbose=verbose)
	model.fit(([train_data[0][0], train_data[0][1]]), train_data[1], batch_size=32, epochs=50, validation_split=0.2)
	# evaluate model on training data
	train_score = evaluate_model(model, train_descriptions, train_features, tokenizer, max_length)
	test_score = evaluate_model(model, test_descriptions, test_features, tokenizer, max_length)
	# store
	train_results.append(train_score)
	test_results.append(test_score)
	print('>%d: train=%f test=%f' % ((i+1), train_score, test_score))
# save results to file
# df = DataFrame()
# df['train'] = train_results
# df['test'] = test_results
# print(df.describe())
# df.to_csv(model_name+'.csv', index=False)

# show some results


result_id = sorted(test)[:20]
result_desc = {key: desc for key, desc in test_descriptions.items() if key in result_id}
result_features = {key: features for key, features in test_features.items() if key in result_id}
evaluate_model(model, result_desc, result_features, tokenizer, max_length, display=True)

# code.interact(local=locals())
