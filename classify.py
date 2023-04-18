import argparse
import shutil
import os

from pycparser import c_parser, preprocess_file, c_ast, c_generator

from typemap import Typemap, DefinitionMap
from visitors import ScopedNodeVisitor

_DEBUG_CODE_SPLITTER = False
_DEBUG_BUILD_TYPEMAP = True

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
        return name in ['FuncDecl', 'Compound', 'For', 'While', 'DoWhile', 'Switch']

    def visit(self, node, id):
        node_name = node.__class__.__name__

        if self.is_scoped_type(node_name):
            if _DEBUG_BUILD_TYPEMAP:
                print ("Entering new scope: ", node_name)
            # Create a new level of nesting in the typemap.
            self.typemaps.add_nest(id, self.current_id)
            self.definition_maps.add_nest(id, self.current_id)

            self.ids_stack.append(self.current_id)

            self.current_id = id
        elif _DEBUG_BUILD_TYPEMAP:
            print("Not entering new scope: ", node_name)

        super().visit(node, id)

    def visit_Decl(self, node, id):
        if _DEBUG_BUILD_TYPEMAP:
            print ("Visiting decl :", node.name)
        self.typemaps.add_type(node.name, node.type, self.current_id)

        # Need to manually recurse -- some defs are
        # e.g. functions
        for typ, child in node.children():
            self.visit(child, self.id_for(child))

    def visit_Typedef(self, node, id):
        self.definition_maps.add(node.name, node.type)

        # Need to manually recurse -- some defs are
        # e.g. functions
        for typ, child in node.children():
            self.visit(child, self.id_for(child))

    def unvisit(self, node, id):
        node_name = node.__class__.__name__

        if self.is_scoped_type(node_name):
            if _DEBUG_BUILD_TYPEMAP:
                print("Exiting scope for ", node_name)

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
        self.nesting_stack = []

    def is_scoped_type(self, name):
        return name in ['Compound', 'For', 'While', 'DoWhile', 'Switch']

    def visit(self, node, id):
        node_name = node.__class__.__name__

        # if entering scope, set it up properly.
        if self.is_scoped_type(node_name):
            self.nesting_stack.append(self.current_nesting)
            self.current_nesting = id
            self.defined_variables[self.current_nesting] = set()

        super().visit(node, id)

    def unvisit(self, node, id):
        node_name = node.__class__.__name__

        # if exiting scope, then wind up the stack.
        if self.is_scoped_type(node_name):
            self.current_nesting = self.nesting_stack.pop()
            del self.defined_variables[self.current_nesting]

        super().unvisit(node, id)

    # check that this is defined
    def visit_ID(self, node, id):
        if self.is_defined(node.name):
            pass
        else:
            self.params.append(node.name)

    # Add a new declaration o
    def visit_Decl(self, node, id):
        self.defined_variables[self.current_nesting].add(node.name)

    # Go through the def stack to figure out if this is currently defined
    def is_defined(self, name):
        current_nest = self.current_nesting
        nest = self.nesting_stack[:]

        # go through the hierachy of type windows.
        while len(nest) > 0:
            if name in self.defined_variables[current_nest]:
                return True
            else:
                current_nest = nest.pop()

        # one last check as self.current_nesting is not included
        # on the stack.
        return name in self.defined_variables[current_nest]


# Generate a function header for a snippet.
# take a typemap that has both the types
# for each variable name and the definitoin lookup
# map so a whole chunk of code can be created.
def generate_functions(snippet, typemap_walk):
    if snippet.__class__.__name__ == 'FuncDef':
        # Already a function :)
        return snippet

    # Build a function header and body.

def get_typemap(code):
    v = BuildTypemap()

    for item_def in code.ext:
        # Note that there is a wee bug by splitting
        # there here, which is that a function may appear
        # to be undefined in its own body.
        v.start_visit(item_def.decl)
        v.start_visit(item_def.body)

    return v


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
    typemap = get_typemap(ast)

    options = generate_options(args, ast)
    functions = generate_functions(args, options, typemap)

    output_options(args, options)
