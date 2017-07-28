from urllib.parse import urlparse


class S3Url:
    """ Wrapper over s3 url.

    Provides easy method to get common parts.
    """

    def __init__(self, url):
        self.url = url

    @property
    def bucket_name(self):
        return urlparse(self.url).netloc

    @property
    def object_key(self):
        return urlparse(self.url).path.lstrip('/')

    @staticmethod
    def is_valid_url(url):
        p = urlparse(url)
        return bool(p.scheme == 's3' and p.netloc)

    @classmethod
    def parse(cls, url):
        if not cls.is_valid_url(url):
            raise ValueError('invalid s3 url {}'.format(url))
        return cls(url)
