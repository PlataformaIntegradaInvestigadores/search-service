from django_neomodel import DjangoNode
from neomodel import StringProperty, UniqueIdProperty


class CursorReference(DjangoNode):
    next_url = StringProperty()
    cursor = UniqueIdProperty()
    current_url = StringProperty()

    class Meta:
        app_label = "scopus_integration"
