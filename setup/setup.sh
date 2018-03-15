#!/bin/sh

#mkdir data
#cd data
#mkdir im2latex-100k
#cd im2latex-100k
# download im2latex-100k dataset
#wget https://zenodo.org/record/56198/files/formula_images.tar.gz
#wget https://zenodo.org/record/56198/files/im2latex_formulas.lst
#wget https://zenodo.org/record/56198/files/im2latex_test.lst
#wget https://zenodo.org/record/56198/files/im2latex_train.lst
#wget https://zenodo.org/record/56198/files/im2latex_validate.lst
#tar zxvf formula_images.tar.gz

# preprocessing latex image
# cd ../../setup
python ./preprocess_images.py --input-dir ../data/im2latex-100k/formula_images --output-dir ../data/images_processed
python ./preprocess_formulas.py --mode normalize --input-file ../data/im2latex-100k/im2latex_formulas.lst --output-file ../data/formulas.norm.lst
python ./preprocess_filter.py --filter --image-dir ../data/images_processed \
					   --label-path ../data/formulas.norm.lst \
					   --data-path ../data/im2latex_train.lst \
					   --output-path ../data/train_filter.lst 
python ./preprocess_filter.py --filter --image-dir ../data/images_processed \
                                           --label-path ../data/formulas.norm.lst \
                                           --data-path ../data/im2latex_validate.lst \
                                           --output-path ../data/validate_filter.lst
python ./preprocess_filter.py --filter --image-dir ../data/images_processed \
                                           --label-path ../data/formulas.norm.lst \
                                           --data-path ../data/im2latex_test.lst \
                                           --output-path ../data/test_filter.lst

# download word embedding
#cd ../data
#wget http://nlp.stanford.edu/data/glove.6B.zip
#unzip -d ./glove.6B glove.6B.zip

