from urllib.parse import urlparse, urlunparse


def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme in ['http', 'https'], result.netloc])
    except ValueError:
        return False


def normalize_url(url):
    parsed_url = urlparse(url)
    normalized_url = urlunparse(
        (parsed_url.scheme, parsed_url.netloc, '', '', '', '')
    )
    return normalized_url
