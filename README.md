# long-predict


## Instalation

```
wget https://github.com/hugowschneider/longdist.py/archive/v1.0.0.tar.gz
tar zxvf v1.0.0.tar.gz
cd long-predict-0.10
python setup.py install
```

## Usage
```
Method implementation for long ncRNAs and PCT distinction. This
application can create and use models base on the method by Schneider et al
(2017).

optional arguments:
  -h, --help            show this help message and exit
  --citation            Prints bibtex citation.
  --version             Prints version number.

Method Paramenters:
  --longs <longs.fa>    Fasta file containing only long non-coding RNAs. This
                        argument is required.
  --pcts <pcts.fa>      Fasta file containing only protein coding transcripts.
                        This argument is required.
  --input <input.fa>    Fasta file containing transcripts to predict with the
                        model
  --kmers <50>          Number of nucleotide pattern frequencies to consider
                        in the model. Default is 50.
  --ratio <0.75>        The ratio of whole dataset that should be used for
                        training. Default is 0.75.
  --size <200>          Mininum sequence size to consider. Default is 200.
  --cv <10>             Number of folds in cross-validation. Default is 10.
  --log2c <-5,15,2>     Set the range of c to
                        2^{begin,...,begin+k*step,...,end}. Default is
                        -5,15,2.
  --log2g <3,-15,-2>    Set the range of g to
                        2^{begin,...,begin+k*step,...,end}. Default is
                        3,-15,-2.
  --processes <5>       Number of parallel processes for parameters search.
                        Default is 4.
  --out_roc <"lncRNA file"x"PCT file"x"kmers"_roc.eps>
                        Name of the output file for the roc Curve. Default is
                        roc.eps.
  --out_csv <"lncRNA file"x"PCT file"x"kmers".csv>
                        Name of the output CSV file containg the results.
                        Default is a name built from the names of both fasta
                        files.
  --out_model <"lncRNA file"x"PCT file"x"kmers".plk>
                        Name of the output file containg the SVM Model.
                        Default is a name built from the names of both fasta
                        files.
  --predict             Just use a predefined model to distinguish long ncRNAs
                        and PCTs in the input fasta file
  --model_config <"lncRNA file"x"PCT file"x"kmers".plk>
                        The file name containg the model configuration
                        properties for prediction.
  --out <"Input File".csv>
                        The output CSV file for the result of the distinction
                        made in the input file.
  --purge               Purge all intermediate files. Intermediate files have
                        ".longdist." in their names. All intermediate files
                        are used to accelerate consecutive runs of the method.
                        Don't purge them if you want to run this method a
                        second time with the same data

```
###Building Models

The following command builds a model with data from two fasta files, one containing
long noncoding RNAs (``test/GRCm38.lncRNA.fa``) and other containing protein coding
(``test/GRCm38.pct.fa``):

```
$ longdist.py --longs test/GRCm38.lncRNA.fa --pcts test/GRCm38.pcts.fa
```

This command line will build a model with 50 nucleotide patterns frequencies (kmers)
and the first ORF relative length. To change the number of kmers, should be included
the parameter ``--kmers``, for example:

```
$ longdist.py --longs test/GRCm38.lncRNA.fa --pcts test/GRCm38.pcts.fa --kmers 10
```

It is also possible to change the training data ratio for building the model with
the parameter ``--ratio``, for example:

```
$ longdist.py --longs test/GRCm38.lncRNA.fa --pcts test/GRCm38.pcts.fa --ratio 0.5
```

The paramenters ``--log2c`` and ``--log2g`` changes the search space for the C and
gamma parameter, for example:

```
$ longdist.py --longs test/GRCm38.lncRNA.fa --pcts test/GRCm38.pcts.fa --log2c 1,15,2 --log2g 3,-1,-1
```

The model build process creates intermediate files to accelerate the build of the
following models. This intermediate files can be deleted with the parameter ``--purge``.
Also, some output files will be created to evaluated model performances. All file names
are based on the input files, for example ``GRCm38.lncRNA_x_GRCm38.pct_50.csv``.

The process outputs the following output files:
- A CSV file with the prediction results;
- An EPS file with the ROC Curve;
- A PLK and a PLK.CONF files. PLK is the SVM Model and the PLK.CONF is the
configuration to use this model.

### Distinguishing lncRNAs and PCTs

To distinguish PCTs and lncRNAs from a input fasta file (``input.fa``) using a pre-built
model (``model.plk.conf``), the following command should be used:

```
$ longdist.py --predict --input input.fa --model_config model.plk.conf
```

This command will create a csv file named ``input.fa.csv`` with the prediction results.

### Models

Models are PLK files built with scikit-learn package and they are only compatible with
the package's SVM implementation. To use the model the PLK.CONF file should be used together
with the model. To move the model to another folder, the PLK.CONF should be moved to.

The selected attributes for the model are listed in the PLK.CONF file.

## Copyright
The work herein is Copyright 20013--2017 Hugo Wruck Schneider and Universidade de Brasília (UnB). **No rights are given to reproduce or modify this work**.

This work uses libSVM for model training and prediction:

Chih-Chung Chang and Chih-Jen Lin, LIBSVM : a library for support vector machines. ACM Transactions on Intelligent Systems and Technology, 2:27:1--27:27, 2011. Software available at [http://www.csie.ntu.edu.tw/~cjlin/libsvm](http://www.csie.ntu.edu.tw/~cjlin/libsvm)