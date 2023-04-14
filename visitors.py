from pycparser import c_parser, preprocess_file, c_ast, c_generator


# This is to allow for scope checking, e.g. to check if varaibles
# are defined.  It has a 'visit' call, and an 'unvisit' call
# that is made when the visits are complete.
class ScopedNodeVisitor(object):
    id = 0 # This ID is different for every call to visit.  It's intended to help
    # you distinguish which unvisit call corresponds to which visit call,
    # not which node is which!
    _method_cache = None

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
        if self._method_cache is None:
            self._method_cache = {}

        unvisitor = self._method_cache.get(node.__class__.__name__, None)
        if unvisitor is None:
            method = 'unvisit_' + node.__class__.__name__
            unvisitor = getattr(self, method, self.generic_visit)

            self._method_cache[node.__class__.__name__] = unvisitor

        return unvisitor(node, visit_id)

    def generic_visit(self, node, this_id):
        for c in node:
            self.id += 1
            self.visit(c, self.id)

        self.unvisit(node, this_id)

    def generic_unvisit(self, node, id):
        pass
