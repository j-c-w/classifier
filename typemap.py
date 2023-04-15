class Typemap(object):
    def __init__(self):
        self.typemap_map = {}
        self.parent_map = {}

        self.parent_map[-1] = -1
        self.typemap_map[-1] = {}

    def add_nest(self, id, parent_id=-1):
        self.typemap_map[id] = {}
        self.parent_map[id] = parent_id

    def unnest(self):
        del self.typemap_map[id]
        del self.parent_map[id]

    def add_type(self, name, type, nest_id):
        self.typemap_map[nest_id][name] = type

    def lookup(self, name, nest):
        nest_id = nest
        while nest_id != -1:
            if name in self.typemap_map[nest_id]:
                return self.typemap_map[nest_id][name]
            else:
                # get parent typemap;
                nest_id = self.parent_map[nest_id]
        if name in self.typemap_map[-1]:
            return self.typemap_map[-1][name]
        else:
            # Failed to find anyting
            return None

# TODO --- implement this properly.
def DefinitionMap(object):
    def __init__(self):
        self.defmap = {}

    def add(self, defname, defdef):
        self.defmap[defname] = defdef

    def lookup(self, defname):
        if defname in self.defmap:
            return self.defmap[defname]

    def add_nest(self, id, parent_id):
        pass # This is what we need to implement

    def unnest(self):
        pass
