from neomodel import FloatProperty, IntegerProperty, StructuredRel


class CoAuthored(StructuredRel):
    shared_pubs = IntegerProperty()
    collab_strength = FloatProperty()
