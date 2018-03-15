#!/bin/sh

mkdir data

# download dataset
wget http://nlp.cs.illinois.edu/HockenmaierGroup/Framing_Image_Description/Flickr8k_Dataset.zip
wget http://nlp.cs.illinois.edu/HockenmaierGroup/Framing_Image_Description/Flickr8k_text.zip
upzip -d ./data/Flickr8k_Dataset Flickr8k_Dataset.zip
unzip -d ./data/Flickr8k_text Flickr8k_text.zip

# setup for descriptions
python setup/setup_descriptions.py

# setup for features
python setup/setup_features.py

# download
wget http://nlp.stanford.edu/data/glove.6B.zip
unzip -d ./data/glove.6B glove.6B.zip
