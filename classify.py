import argparse
import shutil
import os

from pyclibrary import CParser
from pycparser import preprocess_file

class Unimplemented(Exception):
    pass

class DefaultClassifier(object):
    def __init__(self):
        pass

    # return a score between 0.0. and 1.0 for likelyhood of usefulness.
    def score(self, code):
        return 1.0

def load_code(code_path):
    preprocessed = preprocess_file(code_path)
    preprocessed_path = code_path + '.preprocessed.c'
    with open(preprocessed_path, 'w') as f:
        f.write(preprocessed)

    parser = CParser()
    ast = parser.parse(preprocessed_path)

    return ast

def load_classifier(mode):
    # TODO --- properly load based on name provided
    if mode == 'DefaultClassifier':
        return DefaultClassifier()
    raise Unimplemented()

def generate_options(args, code):
    # first load the classifier;
    classifier = load_classifier(args.classification_mode)

    breakpoint()
    funcs = code.defs['functions']
    if args.sub_function:
        # TODO --- gereate all the sane snips.
        raise Unimplemented()
    else:
        snips = funcs

    snip_score_pairs = []
    for snip in snips:
        # Get the score for each snip:
        score = classifier.score(snip)
        snip_score_pairs.append((snip, score))

    # Sort:
    sorted_snips = sorted(snip_score_pairs, key=lambda x: x[1], reverse=True)

    # Return top-N:
    returned = [snip[0] for snip in sorted_snips[:args.number_to_generate]]
    return returned

def output_options(args, options):
    if os.path.exists(args.output_folder):
        shutil.rmtree(args.output_folder)

    os.mkdir(args.output_folder)

    choice = 0
    for opt in options:
        breakpoint()
        with open(args.output_folder + '/' + str(choice) + '.c', 'w') as f:
            f.write(opt)
        choice += 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Snip functions out of C files")

    parser.add_argument("c_file")
    parser.add_argument("--classification-mode", default="DefaultClassifier", dest='classification_mode')

    parser.add_argument('--sub-function', default=False, action='store_true', dest='sub_function')
    parser.add_argument('--number-to-generate', default=10, type=int, dest='number_to_generate')
    parser.add_argument('--output-folder', default='output', dest='output_folder')

    args = parser.parse_args()

    ast = load_code(args.c_file)
    options = generate_options(args, ast)
    output_options(args, options)
