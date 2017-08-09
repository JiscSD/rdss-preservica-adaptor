import pytest

from preservicaservice import meta


@pytest.mark.parametrize(
    'data, contents', [
        (
            (('foo', 'bar',),),
            (
                '<oai_dc:dc xmlns:dc="http://purl.org/dc/elements/1.1/"'
                ' xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"'
                ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
                ' xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/'
                ' http://www.openarchives.org/OAI/2.0/oai_dc.xsd">\n'
                '  <dc:foo>bar</dc:foo>\n'
                '</oai_dc:dc>\n'
            ),
        ),
    ],
)
def test_write_object_meta(temp_file, data, contents):
    meta.write_object_meta(temp_file, data)
    with open(temp_file) as f:
        assert f.read() == contents


@pytest.mark.parametrize(
    'data, contents', [
        (
            {'foo': {'bar': 'baz'}},
            (
                '<?xml version="1.0" encoding="UTF-8" ?>'
                '<root>'
                '<foo type="dict">'
                '<bar type="str">baz</bar>'
                '</foo>'
                '</root>'
            ),
        ),
    ],
)
def test_write_message_meta(temp_file, data, contents):
    meta.write_message_meta(temp_file, data)
    with open(temp_file) as f:
        assert f.read() == contents
