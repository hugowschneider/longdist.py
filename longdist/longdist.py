# -*- coding: utf-8 -*-


"""bootstrap.bootstrap: provides entry point main()."""

__version__ = "1.0.0"

from argparse import ArgumentParser
from .sequence_attributes import SequenceAttributes
import numpy as npy
from sklearn import svm
from sklearn.model_selection import cross_val_score
from .pca_attributes import PCAAttributes
from multiprocessing import Pool
from math import floor
from sklearn import metrics
from sklearn.externals import joblib
import os
import csv
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import zoomed_inset_axes
from mpl_toolkits.axes_grid1.inset_locator import mark_inset
import configparser


def main():
    parser = ArgumentParser(
        description='longdist: Method implementation for long ncRNAs and PCT distinction. This application can create and use models base on the method by Schneider et al (2017).')
    parser.add_argument('--citation', action='store_true', help='Prints bibtex citation.')
    parser.add_argument('--version', action='store_true', help='Prints version number.')
    group = parser.add_argument_group("Method Paramenters")
    group.add_argument('--longs', nargs=1, metavar='<longs.fa>', dest='longs',
                       help='Fasta file containing only long non-coding RNAs. This argument is required.')
    group.add_argument('--pcts', nargs=1, metavar='<pcts.fa>', dest='pcts',
                       help='Fasta file containing only protein coding transcripts. This argument is required.')
    group.add_argument('--input', nargs=1, metavar='<input.fa>', dest='input',
                       help='Fasta file containing transcripts to predict with the model')

    group.add_argument('--kmers', nargs=1, metavar='<50>', default=50, type=int, dest='kmers',
                       help='Number of nucleotide pattern frequencies to consider in the model. Default is 50.')

    group.add_argument('--ratio', nargs=1, metavar='<0.75>', default=0.75, type=float, dest='fraction',
                       help='The ratio of whole dataset that should be used for training. Default is 0.75.')

    group.add_argument('--size', nargs=1, metavar='<200>', default=200, type=int, dest='size',
                       help='Mininum sequence size to consider. Default is 200.')
    group.add_argument('--cv', nargs=1, metavar='<10>', default=10, type=int, dest='cross_validation',
                       help='Number of folds in cross-validation. Default is 10.')

    group.add_argument('--log2c', nargs=1, metavar='<-5,15,2>', default="-5,15,2",
                       help='Set the range of c to 2^{begin,...,begin+k*step,...,end}. Default is -5,15,2.')

    group.add_argument('--log2g', nargs=1, metavar='<3,-15,-2>', default="3,-15,-2",
                       help='Set the range of g to 2^{begin,...,begin+k*step,...,end}. Default is 3,-15,-2.')

    group.add_argument('--processes', nargs=1, metavar='<5>', default=4, type=int,
                       help='Number of parallel processes for parameters search. Default is 4.')

    group.add_argument('--out_roc', nargs=1, metavar='<"lncRNA file"x"PCT file"x"kmers"_roc.eps>', dest='roc_file',
                       help='Name of the output file for the roc Curve. Default is roc.eps.')

    group.add_argument('--out_csv', nargs=1, metavar='<"lncRNA file"x"PCT file"x"kmers".csv>', dest='csv_file',
                       help='Name of the output CSV file containg the results. Default is a name built from the names of both fasta files.')

    group.add_argument('--out_model', nargs=1, metavar='<"lncRNA file"x"PCT file"x"kmers".plk>',
                       dest='model_file',
                       help='Name of the output file containg the SVM Model. Default is a name built from the names of both fasta files.')

    group.add_argument('--predict', action="store_true",
                       help='Just use a predefined model to distinguish long ncRNAs and PCTs in the input fasta file')

    group.add_argument('--model_config', nargs=1, metavar='<"lncRNA file"x"PCT file"x"kmers".plk>',
                       dest='model_config',
                       help='The file name containg the model configuration properties for prediction.')

    group.add_argument('--out', nargs=1, metavar='<"Input File".csv>',
                       dest='output',
                       help='The output CSV file for the result of the distinction made in the input file.')

    group.add_argument('--purge', action="store_true",
                       help='Purge all intermediate files. Intermediate files have ".longdist." in their names.'
                            ' All intermediate files are used to accelerate consecutive runs of the method. '
                            'Don\'t purge them if you want to run this method a second time with the same data')

    args = parser.parse_args()

    if args.citation:
        print("""@artile {Schneider:2017,
         title={A Support Vector Machine based method to distinguish long non-coding RNAs from protein coding transcripts},
         author={Schneider, Hugo and Raiol, Tainá and Brígido, Marcelo and Walter, Maria E. M. T. and Stadler, Peter },
         year={2017}
}""")
    elif args.version:
        print(parser.description)
        print("Version: %s" % __version__)

    else:
        if args.predict:
            if args.input and args.model_config:
                predict(args)
            else:
                print("--input and --model_config parameters are required for prediction")
        elif args.longs and args.pcts:
            print(parser.description)
            create_model(args)
        else:
            parser.print_usage()


def predict(args):
    config = configparser.ConfigParser()
    config.read(args.model_config[0])
    kmers = eval(config['MODEL']['attributes'])
    input = SequenceAttributes(input_file=args.input[0], size=args.size, clazz=-1, use_intermediate_file=False)
    input.process(kmers)

    clf = joblib.load(os.path.join(os.path.split(args.model_config[0])[0],config['MODEL']['model']))

    X = input.data[npy.array(kmers)].copy(npy.float_).reshape(input.data.shape + (-1,))

    probabilities = clf.predict_proba(X)

    csv_file = args.output if args.output else "%s.csv" % args.input[0]

    dump_result_csv(input.data["id"], probabilities[:, 1], probabilities[:, 0], csv_file)

    if args.purge:
        purge([input.intermediate_file()])


def create_model(args):
    longs = SequenceAttributes(input_file=args.longs[0], size=args.size, clazz=1)
    pcts = SequenceAttributes(input_file=args.pcts[0], size=args.size, clazz=0)
    print("Processing fasta files. This could take some minutes... (if you don't have some intermediate files)")
    print("Processing long non-coding RNA fasta file...")
    longs.process()
    print("Processing proteing coding transcripts fasta file...")
    pcts.process()

    min_size = min([len(longs.data), len(pcts.data)])

    longs_data_training, longs_data_testing = section(longs.data, min_size, args.fraction)
    pcts_data_training, pcts_data_testing = section(pcts.data, min_size, args.fraction)

    training = npy.hstack((longs_data_training, pcts_data_training))
    testing = npy.hstack((longs_data_testing, pcts_data_testing))

    pca = PCAAttributes(training)
    kmers = pca.attributes(args.kmers)

    labels = training["class"]
    attributes = training[npy.array(["fp"] + kmers)]
    x = attributes.copy(npy.float_)
    attributes = x.reshape(attributes.shape + (-1,))

    testing_labels = testing["class"]
    testing_attributes = testing[npy.array(["fp"] + kmers)]
    x = testing_attributes.copy(npy.float_)
    testing_attributes = x.reshape(testing_attributes.shape + (-1,))

    base_name = build_base_name(args.longs[0], args.pcts[0], args.kmers)
    grid_file_name = "%s.longdist.npy" % base_name

    model_file = args.model_file if args.model_file  else "%s.plk" % base_name
    model_config_file = "%s.conf" % model_file
    csv_file = args.csv_file if args.csv_file   else "%s.csv" % base_name
    roc_file = args.roc_file if args.roc_file   else "%s_roc.eps" % base_name

    if os.path.exists(model_file):
        clf = joblib.load(model_file)
    else:
        c, gamma = svm_model_selection(attributes, labels, args.cross_validation, args.log2c, args.log2g,
                                       args.processes, grid_file_name)
        clf = svm.SVC(kernel='rbf', C=c, gamma=gamma, probability=True)
        clf.fit(attributes, labels)
        joblib.dump(clf, model_file)

    probabilities = clf.predict_proba(testing_attributes)
    long_probabilities = probabilities[:, 1]

    false_positive_rate, true_positive_rate, _ = metrics.roc_curve(testing_labels, long_probabilities)
    auc = metrics.auc(false_positive_rate, true_positive_rate)
    accuracy, sensitivity, specificity = accuracy_sensitivity_specificity(testing_labels, long_probabilities)

    dump_result_csv(testing["id"], long_probabilities, probabilities[:, 0], csv_file)
    roc(false_positive_rate, true_positive_rate, "AUC: %.2f%%" % (auc * 100),
        "%s x %s\nAccuracy: %.2f%% | Sensitivity: %.2f%% | Specificity: %.2f%%" % (
            os.path.basename(args.longs[0]), os.path.basename(args.pcts[0]), 100 * accuracy, 100 * sensitivity,
            100 * specificity), roc_file)

    config = configparser.ConfigParser()
    config['MODEL'] = {
        'desc': "Model built with lncRNA data from '%s' and PCT data from '%s'" % (
            os.path.basename(args.longs[0]), os.path.basename(args.pcts[0])),
        'attributes': ['fp'] + kmers,
        'model': os.path.relpath(model_file, os.path.split(model_config_file)[0])
    }

    with open(model_config_file, 'w') as config_file:
        config.write(config_file)
        args.model_config = [model_config_file]

    if args.purge:
        purge([grid_file_name, longs.intermediate_file(), pcts.intermediate_file()])

    if args.input:
        predict(args)


def purge(files):
    for f in files:
        os.remove(f)

def roc(false_positive_rate, true_positive_rate, label, title, file_name):
    fig, ax = plt.subplots()
    axins = zoomed_inset_axes(ax, 3.2, loc=7)

    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1])

    ax.plot(false_positive_rate, true_positive_rate, label=label)
    axins.plot(false_positive_rate, true_positive_rate, label=label)

    axins.set_xlim(0.0, 0.1)  # apply the x-limits
    axins.set_ylim(0.9, 1)

    mark_inset(ax, axins, loc1=1, loc2=3, fc="none", ec="0.5")

    ax.plot([0, 1], [0, 1], 'k--')

    ax.set_xlabel('False positive rate')
    ax.set_ylabel('True positive rate')
    ax.set_title(title)
    ax.legend(loc=4)
    plt.savefig(file_name, format='eps')


def accuracy_sensitivity_specificity(labels, probabilities):
    pred = npy.copy(probabilities)
    pred[pred < 0.5] = 0
    pred[pred >= 0.5] = 1

    accuracy = metrics.accuracy_score(labels, pred)
    confusion_matrix = metrics.confusion_matrix(labels, pred)
    TP = confusion_matrix[1, 1]
    TN = confusion_matrix[0, 0]
    FP = confusion_matrix[0, 1]
    FN = confusion_matrix[1, 0]
    sensitivity = float(TP) / float(FN + TP)
    specificity = float(TN) / float(TN + FP)

    return accuracy, sensitivity, specificity


def dump_result_csv(ids, long_probabilities, pct_probabilities, file):
    with open(file, 'w') as csvfile:
        fieldnames = ['sequence', 'pct %', 'lncRNA %']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for (id, lp, pp) in zip(ids, long_probabilities, pct_probabilities):
            writer.writerow({'sequence': id, 'pct %': pp, 'lncRNA %': lp})


def build_base_name(long_file, pct_file, kmers):
    long_file_base = '.'.join(os.path.basename(long_file).split(sep='.')[:-1])
    pct_file_base = '.'.join(os.path.basename(pct_file).split(sep='.')[:-1])

    return os.path.join(os.path.split(long_file)[0], "%s_x_%s_%d" % (long_file_base, pct_file_base, kmers))


def svm_model_selection(attributes, labels, folds, log2c, log2g, processes, file_name):
    c_begin, c_end, c_step = map(int, log2c.split(','))
    g_begin, g_end, g_step = map(int, log2g.split(','))

    pool = Pool(processes)

    if os.path.exists(file_name):
        results = npy.asarray(npy.load(file_name))
    else:
        results = []

    def callback(result):
        results.append(result)

        print("C=%.13f, Gamma=%.13f: Accuracy=%.13f" % (
            result[0], result[1], result[2]))
        npy.save(file_name, npy.array(results))

    for log2c in range(c_begin, c_end, c_step):
        for log2g in range(g_begin, g_end, g_step):
            c, gamma = 2 ** log2c, 2 ** log2g
            if len(results) > 0:
                n_array = npy.array(results)
                index = npy.where(npy.all(n_array[:, :2] == npy.array([c, gamma]), axis=1))
                if len(index) > 0 and len(index[0]):
                    print("C=%.13f, Gamma=%.13f: Accuracy=%.13f (Restored from intermediate file)" % (
                        c, gamma, n_array[index[0], 2]))
                    continue

            pool.apply_async(cross_validation, args=(c, gamma, attributes, labels, folds),
                             callback=callback)

    pool.close()
    pool.join()

    results = npy.array(results)
    npy.save(file_name, results)

    best_models = results[results[:, 2] == npy.amax(results[:, 2])]

    best_models = best_models[best_models[:, 0] == npy.amin(best_models[:, 0])]
    [c, gamma, _] = best_models[0]

    return c, gamma


def cross_validation(c, gamma, attributes, labels, folds):
    clf = svm.SVC(kernel='rbf', C=c, gamma=gamma)
    scores = cross_val_score(clf, attributes, labels, cv=folds)

    return [c, gamma, npy.max(scores)]


def section(data, size, fraction):
    if len(data) == size:
        remaining_data = data
    else:
        idx = npy.random.randint(len(data), size=size)
        remaining_data = data[idx]

    idx = npy.random.randint(size, size=int(floor(size * fraction)))
    mask = npy.ones(size, npy.bool)
    mask[idx] = 0

    return remaining_data[idx], remaining_data[mask]