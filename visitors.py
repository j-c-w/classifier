from pycparser import c_parser, preprocess_file, c_ast, c_generator


# Get the ID for a particular node --- not too sure
# what the best starteguye is here.
def _id_for(node):
    return hash(node)

# This is to allow for scope checking, e.g. to check if varaibles
# are defined.  It has a 'visit' call, and an 'unvisit' call
# that is made when the visits are complete.
class ScopedNodeVisitor(object):
    _method_cache = None
    _unvisit_method_cache = None

    def id_for(self, node):
        return _id_for(node)

    def start_visit(self, node):
        self.visit(node, _id_for(node))

    def visit(self, node, visit_id):
        if self._method_cache is None:
            self._method_cache = {}

        visitor = self._method_cache.get(node.__class__.__name__, None)
        if visitor is None:
            method = 'visit_' + node.__class__.__name__
            visitor = getattr(self, method, self.generic_visit)

            self._method_cache[node.__class__.__name__] = visitor

        return visitor(node, visit_id)

    def unvisit(self, node, visit_id):
        if self._unvisit_method_cache is None:
            self._unvisit_method_cache = {}

        unvisitor = self._unvisit_method_cache.get(node.__class__.__name__, None)
        if unvisitor is None:
            method = 'unvisit_' + node.__class__.__name__
            unvisitor = getattr(self, method, self.generic_unvisit)

            self._unvisit_method_cache[node.__class__.__name__] = unvisitor

        return unvisitor(node, visit_id)

    def generic_visit(self, node, this_id):
        for ty, c in node.children():
            id = _id_for(node)
            self.visit(c, id)

        self.unvisit(node, this_id)

    def generic_unvisit(self, node, id):
        pass
