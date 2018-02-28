import logging
import os
import requests
import sys


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

logging.info('Fetching token...')
token_response = requests.post(
    base_url + 'api/accesstoken/login', params={
        'tenant': tenant,
        'username': username,
        'password': password,
    },
)
logging.info(token_response.json())
