import argparse
import shutil
import os

from pycparser import c_parser, preprocess_file, c_ast, c_generator

_DEBUG_CODE_SPLITTER = False

class Unimplemented(Exception):
    pass

class DefaultClassifier(object):
    def __init__(self):
        pass

    # return a score between 0.0. and 1.0 for likelyhood of usefulness.
    def score(self, code):
        return 1.0


class FunctionSplitter(c_ast.NodeVisitor):
    def __init__(self):
        super().__init__()

        self.funs = []

    def visit_FuncDef(self, node):
        self.funs.append(node)

class CodeSplitter(c_ast.NodeVisitor):
    def __init__(self):
        super().__init__()

        self.snips = []

    # Return whether this is a snipable type.
    # Most types are not snippable --- compound is
    # dealt with as a special case.
    def is_snippable_type(self, node):
        name = node.__class__.__name__

        return name in ['For', 'While', 'Case', 'DoWhile', 'Enumerator', 'If']

    def visit(self, node):
        # Check if this is a sane node to split out:
        generator = c_generator.CGenerator()
        if _DEBUG_CODE_SPLITTER:
            print("Visiting node type ", node.__class__.__name__)
            print("Visiting ", generator.visit(node))

        if self.is_snippable_type(node):
            self.snips.append(node)

        super().visit(node)

    # Special case for visiting a sequence: we add
    # every ordered subsequence, not every sequence
    # in total.
    def visit_Compound(self, node):
        child_seqs = []

        for (name, node) in node.children():
            child_seqs.append(node)

        # Add every subset of this.
        for i in range(0, len(child_seqs)):
            for j in range(0, len(child_seqs)):
                if i < j:
                    new_compound = c_ast.Compound(child_seqs[i:j])
                    self.snips.append(new_compound)

        # Recurse as normal.
        super().generic_visit(node)

# Build a typemap.  The typemap goes from nesting number -> name -> ID.
# 
class BuildTypemap(ScopedNodeVisitor):
    def __init__(self):
        super().__init__()

        self.typemaps = Typemap()
        self.current_id = -1
        self.definition_maps = DefinitionMap()
        self.ids_stack = []

    def is_scoped_type(self, name):
        return name in ['Compound', 'For', 'While', 'DoWhile', 'Switch']

    def visit(self, node, id):
        node_name = node.__class__.__name__

        if is_scoped_type(node_name):
            # Create a new level of nesting in the typemap.
            self.typemaps.add_nest(id, self.current_id)
            self.definition_maps.add_nest(id, self.current_id)

            self.ids_stack.push(self.current_id)

            self.current_id = id

        super().visit(node, id)

    def visit_Decl(self, node, id):
        self.typemaps.add(node.name, node.type)

    def visit_Typedef(self, node, id):
        self.definition_maps.add(node.name, node.type)

    def unvisit(self, node, id):
        node_name = node.__class__.__name__

        if is_scoped_type(node_name):
            self.typemaps.unnest()
            self.definition_maps.unnest()

        self.current_id = self.ids_stack.pop()
        super().unvisit(node, id)

# Given a snip, get the undefined components of
# that function: split into parameters that should
# be passed and types that need to be defined.
class GetParams(ScopedNodeVisitor):
    def __init__(self):
        super().__init__()

        self.params = []
        # Dict from scoping to the set of vairables
        # defined at that nesting.
        self.defined_variables = {}
        self.current_nesting = -1 # IDs start from 0.

    def is_scoped_type(self, name):
        TODO
        return name in ['']

    def visit(self, node):
        node_name = node.__class__.__name__

        if self.is_scoped_type(node_name):


class GetTypes(c_ast.NodeVisitor):
    def __init__(self):
        super().__init__()

        self.types = []

# Generate a function header for a snippet.
def generate_function(snippet):
    if snippet.__class__.__name__ == 'FuncDef':
        # Already a function :)
        return snippet

    visitor = 

def load_code(code_path):
    preprocessed = preprocess_file(code_path)
    parser = c_parser.CParser()
    ast = parser.parse(preprocessed)

    return ast

def load_classifier(mode):
    # TODO --- properly load based on name provided
    if mode == 'DefaultClassifier':
        return DefaultClassifier()
    raise Unimplemented()

def generate_options(args, code):
    # first load the classifier;
    classifier = load_classifier(args.classification_mode)

    if args.sub_function:
        # TODO --- gereate all the sane snips.
        v = CodeSplitter()
        v.visit(code)
        snips = v.snips
    else:
        v = FunctionSplitter()
        v.visit(code)
        snips = v.funs

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

    generator = c_generator.CGenerator()

    choice = 0
    for opt in options:
        with open(args.output_folder + '/' + str(choice) + '.c', 'w') as f:
            f.write(generator.visit(opt))
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
