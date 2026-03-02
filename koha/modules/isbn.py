""" Python Scripts to import metadata from ISBNs, using libisbn and Google API """

import sys

sys.path.append("./modules")  # importing custom functions in modules

from modules.utilities import *

from isbnlib import meta
from isbnlib.registry import bibformatters
from isbnlib import canonical, is_isbn10, is_isbn13
from isbnlib import config, registry


def get_metadata_from_google_api(isbn, google_api_key):
    GB_API_URL = "https://www.googleapis.com/books/v1/volumes"
    session = requests.Session()
    session.headers.update(
        {"User-Agent": "google-books-metadata/1.0 (+https://example.org)"}
    )
    params = {"q": f"isbn:{isbn}", "key": google_api_key}
    response = session.get(GB_API_URL, params=params, timeout=10)
    """# Debugging
    print("REQUEST URL:", response.request.url)
    print("REQUEST HEADERS:", response.request.headers)
    print("REQUEST BODY (bytes):", response.request.body)
    print("STATUS:", response.status_code)
    print("RESPONSE HEADERS:", response.headers)
    print("RESPONSE TEXT:", (response.text or ""))
	"""

    return response.json()


def get_metadata_from_isbn(
    isbn, google_api_key, services=["goob", "openl", "wiki"], metadata_format="csl"
):
    # canonical form of isbn input
    isbn = canonical(isbn)

    # set up metadata format
    out_format = bibformatters[metadata_format]

    metadata = []

    for service in services:
        if service == "goob":
            # config.add_apikey("goob", google_api_key) not working, giving 429 error
            metadata.append(get_metadata_from_google_api(isbn, google_api_key))
            print(f"Service {service}: \n {metadata[-1]} \n")
        try:
            metadata.append(out_format(meta(isbn, service=service)))
            print(f"Service {service}: \n {metadata[-1]} \n")

        except Exception:
            pass
