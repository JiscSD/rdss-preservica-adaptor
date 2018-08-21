import boto3
import urllib
import requests
import unicodedata
from base64 import b64decode
from lxml import etree
from Crypto.Cipher import AES


class PreservicaBucketAPI(object):

    """ Interacts with the Preservica API to get a list of bucket names and 
        IAM credentials. """

    BUCKET_DETAILS_ENDPOINT = '/api/s3/bucketdetails?source=legitimate'
    BUCKET_DETAILS_MAP = {
        'aws_access_key_id': '/dataSources/a/text()',
        'aws_secret_access_key': '/dataSources/b/text()',
        'aws_session_token': '/dataSources/c/text()',
        'bucket_names': '/dataSources/sipLocations/sipLocation/text()',
    }

    def __init__(
        self,
        preservica_url,
        preservica_decryption_key_utf8,
    ):
        self.preservica_url = preservica_url
        preservica_decryption_key = bytes(preservica_decryption_key_utf8, 'utf-8')
        self.cipher = AES.new(preservica_decryption_key, AES.MODE_ECB)

    def _decrypt_string(self, string):
        b64_str = b64decode(string)
        decrypted_b64 = self.cipher.decrypt(b64_str)
        return decrypted_b64.decode('utf-8')

    def _strip_control_characters(self, string):
        """ Removes unicode control characters from the decrypted strings.
            There are lots of these littering the output - 
            may be undocumented random padding pre-encryption?
            """
        def not_ctrl_char(char): return unicodedata.category(char)[0] != 'C'
        return ''.join(filter(not_ctrl_char, string))

    def _get_encrypted_bucket_details(self, preservica_user, preservica_password):
        url = urllib.parse.urljoin(self.preservica_url, self.BUCKET_DETAILS_ENDPOINT)
        return requests.get(url, auth=(preservica_user, preservica_password))

    def _preservica_xml_to_etree(self, response):
        # Some munging to get the response contents as parseable bytes
        xml_bytes = response.content.decode('unicode_escape').lstrip('"').rstrip('"').encode()
        # The XML has a header stating it's UTF-16, but it needs parsed as UTF-8
        parser = etree.XMLParser(encoding='UTF-8')
        return etree.fromstring(xml_bytes, parser=parser)

    def get_bucket_details(self, preservica_user, preservica_password):
        encrypted_response = self._get_encrypted_bucket_details(
            preservica_user, preservica_password,
        )
        encrypted_etree = self._preservica_xml_to_etree(encrypted_response)
        tree = etree.ElementTree(encrypted_etree)
        bucket_details = dict()
        for key, xpath in self.BUCKET_DETAILS_MAP.items():
            dec_strs = [
                self._strip_control_characters(self._decrypt_string(s))
                for s in encrypted_etree.xpath(xpath)
            ]
            if len(dec_strs) == 1:
                bucket_details[key] = dec_strs[0]
            else:
                bucket_details[key] = dec_strs
        return bucket_details


class PreservicaS3BucketBuilder(object):

    def __init__(self, preservica_url, environment):
        self.environment = environment
        self.ssm_client = boto3.client('ssm')

        decryption_key = self._get_ssm_value('api-decryption-key')
        self.preservica_bucket_api = PreservicaBucketAPI(
            preservica_url,
            decryption_key,
        )

    def _get_ssm_value(self, *args):
        prefix = ['preservica-adaptor', self.environment]
        key = '-'.join(prefix + list(args))
        return self.ssm_client.get_parameter(
            Name=key,
            WithDecryption=True,
            )['Parameter']['Value'].split(':')[-1]

    def _fetch_preservica_credentials(self, jisc_id):
        """ Get this institutions preservica adaptor credentials to query API."""
        preservica_user = self._get_ssm_value(jisc_id, 'preservica-user')
        preservica_password = self._get_ssm_value(jisc_id, 'preservica-password')
        return preservica_user, preservica_password

    def _select_adaptor_bucket(self, jisc_id, bucket_names):
        """ """
        bucket_name = "com.preservica.rdss.{}.preservica_adaptor".format(jisc_id)
        if bucket_name in bucket_names:
            return bucket_name
        else:
            return

    def get_bucket(self, jisc_id):
        credentials = self._fetch_preservica_credentials(jisc_id)
        bucket_details = self.preservica_bucket_api.get_bucket_details(*credentials)
        bucket_name = self._select_adaptor_bucket(jisc_id, bucket_details.pop('bucket_names', []))
        client = boto3.resource('s3', **bucket_details)
        return client.Bucket(bucket_name)
