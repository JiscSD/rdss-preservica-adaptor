from dicttoxml import dicttoxml
from lxml import etree

DC_NAMESPACE = 'http://purl.org/dc/elements/1.1/'

NSMAP = {
    'dc': DC_NAMESPACE,
    'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
    'xml': 'xml',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
}

ATTRIB = {
    '{http://www.w3.org/2001/XMLSchema-instance}schemaLocation':
        'http://www.openarchives.org/OAI/2.0/oai_dc/ '
        'http://www.openarchives.org/OAI/2.0/oai_dc.xsd',
}

CONTAINER_ELEMENT = '{http://www.openarchives.org/OAI/2.0/oai_dc/}dc'


def write_object_meta(file_path, data):
    """ Generate meta xml from inputs

    :param str file_path: path to write
    :param data: contents
    :type data: Generator of (str, str)
    :return:
    """

    root = etree.Element(CONTAINER_ELEMENT, nsmap=NSMAP, attrib=ATTRIB)

    for key, value in data:
        elem = etree.Element('{{{0}}}{1}'.format(DC_NAMESPACE, key))
        elem.text = value
        root.append(elem)

    contents = etree.tostring(root, pretty_print=True).decode('utf-8')
    with open(file_path, 'w') as f:
        f.write(contents)


def write_message_meta(file_path, data):
    """ Generate root meta data file

    :param str file_path: path to write
    :param dict data: contents to generate xml
    :return:
    """
    contents = dicttoxml(data).decode('utf-8')
    contents = contents.replace(
        '<root>', '<root schemaURI="http://jisc.ac.uk/#rdss/schema">',
    )
    with open(file_path, 'w') as f:
        f.write(contents)
