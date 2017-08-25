# long-predict

## Instalation
```
wget https://github.com/hugowschneider/long-predict/archive/v0.10.tar.gz
tar zxvf v0.10.tar.gz
cd long-predict-0.10
cmake .
make
```
## Usage
```
Usage: ./long_predict [-a] [-c <model config file>] -i <fasta file> [-d <-|+>] [-s <size>] [-o <output file>]
	-a	Attributes only. Output the frequencies of nucleotides patterns and orf size and relation to 
		transcript size.
		The model file will determine the nucleotides patterns will be used, if not present, all
		patterns will be calculated
	-c	Model config file. File specifying the libSVM model and the used attributes
	-d	Direction '+' or '-'. The direction of the fasta file sequences for prediction. '+' will
		read the sequences as is. And '-' will use the complementary sequence. Default '+'
	-i	Input Fasta file for prediction. This file should be a plain text or a gzip fasta
		file
	-o	Output file. The file where the predictions or the attributes will be saved
	-s	Size limit. This attribute ignore sequences shorter than this limit. Default 200

Model Config File is a plain text file containing the following attributes:
	modelFile	The path to the model file. It can be relative to the config file or
	dect	The model description
	attributes	The list of attributes used in the model training. This attributes are valid
				nucleotide frequencies, for example 'aa' and 'atc', and the values 'ol' for
				first ORF lenght and 'op' for first ORF percentage of the corresponding transcript
				length
Ex.:
modelFile=human.model
attributes=aa,aaa,ac,aca,acg,op
```
###Prediction

To classify all sequences in the file `human.fa.gz` using the configuration file located in 
`models/human.model.conf`: 

```
./long_predict -c models/human.model.conf -i human.fa.gz -o output.csv
```

This outputs the following:

```
Predicted lncRNAs: 40.00% (40/100)
```

And it creates the csv file `output.csv` containing all probalities for the prediction:
```
ID,Size,Classification,Probability lncRNA,Probability PCT
"ENST00000437894",227,lncRNA,0.9973536549711840,0.0026463450288160
...
```

###Attributes calculation

To calculate all metrics in the file `human.fa.gz` using the configuration file located in 
`models/human.model.conf`: 

```
./long_predict -a -c models/human.model.conf -i human.fa.gz -o output.csv
```

And it creates the csv file `output.csv` containing all frequencies:
```
ID,a,g,c,t,aa,ac, ...
"ENST00000437894",0.213,0.321,0.124,0.342,0.0026463450288160,0.018462, ...
...
```

If the configuration file is ommited, all possible di-, tri- , tetra-nucleotide pattern frquencies, first ORF length, first ORF relative length, longest ORF length and longest ORF relative length are calculated.



## Copyright
The work herein is Copyright 20013--2016 Hugo Wruck Schneider and Universidade de Brasília (UnB). **No rights are given to reproduce or modify this work**.

This work uses libSVM for model training and prediction:

Chih-Chung Chang and Chih-Jen Lin, LIBSVM : a library for support vector machines. ACM Transactions on Intelligent Systems and Technology, 2:27:1--27:27, 2011. Software available at [http://www.csie.ntu.edu.tw/~cjlin/libsvm](http://www.csie.ntu.edu.tw/~cjlin/libsvm)