import pytz
import requests
import tldextract
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

utc_zone = pytz.timezone('UTC')
cst_zone = pytz.timezone('America/Chicago')


def extract_base_domain(url):
    extracted = tldextract.extract(url)
    base_domain = "{}.{}".format(extracted.domain, extracted.suffix)
    return base_domain


def create_session():
    retry_strategy = Retry(
        total=3,  # Total number of retries to allow
        status_forcelist=[429, 500, 502, 503, 504],  # A set of HTTP status codes to retry
        allowed_methods=["HEAD", "GET", "OPTIONS"],  # Allow retries for these HTTP methods
        backoff_factor=1,  # Wait 2 seconds between retries
        raise_on_status=False,  # Do not raise an exception for status codes in status_forcelist
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session