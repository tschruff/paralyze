from xml.etree import ElementTree
from xml.dom import minidom


def prettiefy(element, encoding='utf-8'):
    rough = ElementTree.tostring(element, encoding=encoding).decode()
    return minidom.parseString(rough).toprettyxml(encoding=encoding)
