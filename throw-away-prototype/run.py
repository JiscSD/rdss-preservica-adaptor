import logging
import os
import requests
import sys
import uuid
from lxml import (
    etree,
)


stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(
    logging.Formatter(
        '%(name)s - %(levelname)s - %(message)s',
    ),
)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(stream_handler)

base_url = os.environ['BASE_URL']
tenant = os.environ['TENANT']
username = os.environ['USERNAME']
password = os.environ['PASSWORD']
namespace_xip = 'http://www.tessella.com/XIP/v4'

logging.info('Fetching token...')
token_response = requests.post(
    base_url + 'api/accesstoken/login', params={
        'tenant': tenant,
        'username': username,
        'password': password,
    },
)
logging.info(token_response.json())

token = token_response.json()['token']

logging.info('Finding root collections before creation...')
find_collections_before_create_response = requests.get(
    base_url + 'api/entity/collections/',
    headers={
        'Preservica-Access-Token': token,
    },
)
collections_before_create = etree.fromstring(find_collections_before_create_response.text.encode('utf-8')).findall(
    './/{{{0}}}Collection'.format(namespace_xip),
)
logging.info('Found %s collections', len(collections_before_create))

logging.info('Creating root collection...')
root_collection_code = str(uuid.uuid4())
root_collection_title = str(uuid.uuid4())
create_root_collection_response = requests.post(
    base_url + 'api/entity/collections/',
    headers={
        'Preservica-Access-Token': token,
    },
    params={
        'parentRef': '@root@',
        'collectionCode': root_collection_code,
        'title': root_collection_title,
        'securityTag': 'open',
    },
)
logging.info(create_root_collection_response.text)

root_collection_ref = etree.fromstring(create_root_collection_response.text.encode('utf-8')).find(
    './/{{{0}}}CollectionRef'.format(namespace_xip),
).text

logging.info('Creating child collection...')
child_collection_code = str(uuid.uuid4())
child_collection_title = str(uuid.uuid4())
create_child_collection_response = requests.post(
    base_url + 'api/entity/collections/',
    headers={
        'Preservica-Access-Token': token,
    },
    params={
        'parentRef': root_collection_ref,
        'collectionCode': child_collection_code,
        'title': child_collection_title,
        'securityTag': 'open',
    },
)
logging.info(create_child_collection_response.text)

logging.info('Finding root collections after creation...')
find_collections_after_create_response = requests.get(
    base_url + 'api/entity/collections/',
    headers={
        'Preservica-Access-Token': token,
    },
)
collections_after_create = etree.fromstring(find_collections_after_create_response.text.encode('utf-8')).findall(
    './/{{{0}}}Collection'.format(namespace_xip),
)
logging.info('Found %s root collections', len(collections_after_create))
assert len(collections_after_create) == len(collections_before_create) + 1
