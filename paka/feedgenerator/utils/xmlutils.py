"""
Utilities for XML generation/parsing.
"""

import re
import operator
import collections
from xml.sax.saxutils import XMLGenerator


class UnserializableContentError(ValueError):
    pass


_order_attrs_key = operator.itemgetter(0)


def _order_attrs(attrs):
    return collections.OrderedDict(
        sorted(attrs.items(), key=_order_attrs_key))


class SimplerXMLGenerator(XMLGenerator):

    def startElement(self, name, attrs):
        return XMLGenerator.startElement(self, name, _order_attrs(attrs))

    def startElementNS(self, name, qname, attrs):
        return XMLGenerator.startElementNS(
            self, name, qname, _order_attrs(attrs))

    def addQuickElement(self, name, contents=None, attrs=None):
        "Convenience method for adding an element with no children"
        if attrs is None:
            attrs = {}
        self.startElement(name, attrs)
        if contents is not None:
            self.characters(contents)
        self.endElement(name)

    def characters(self, content):
        if content and re.search(r'[\x00-\x08\x0B-\x0C\x0E-\x1F]', content):
            # Fail loudly when content has control chars (unsupported in XML 1.0)
            # See http://www.w3.org/International/questions/qa-controls
            raise UnserializableContentError("Control characters are not supported in XML 1.0")
        XMLGenerator.characters(self, content)
