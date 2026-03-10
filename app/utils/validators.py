import re
from urllib.parse import urlparse


def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False


def is_valid_slug(slug: str) -> bool:
    return bool(re.match(r"^[a-zA-Z0-9_-]{3,50}$", slug))
