# Koha API
import requests
from requests_oauth2client import OAuth2Client, OAuth2ClientCredentialsAuth
import json, csv


### KOHA API


def oauth2_session(
    client_id: str, client_secret: str, user_agent: str, base_url: str, scope="all"
):
    """Returns an OAuth2 session, given client ID and secret key of your Koha account.

    Args:
                    client_id (str): Client ID associated with your Koha Admin User.
                    client_secret (str): Secret key provided by the Koha Administration.
                    user_agent (str): User-Agent string. Default is None.
                    base_url (str): Base URL for your Koha Staff interface

    Returns:
                    session (oauth2): OAuth2 session

    Examples:
                    >>> my_session = pyreslib.koha.oauth2_session(client_id="{CLIENT_ID}"", client_secret="{SECRET_KEY}" , base_url="https://{KOHA_STAFF_URL}/api/v1")

    """
    token_url = f"{base_url}/oauth/token"  # This may be different for your endpoint

    oauth2client = OAuth2Client(
        token_endpoint=token_url, client_id=client_id, client_secret=client_secret
    )
    # Force the User-Agent before authorization
    if user_agent is not None:
        oauth2client.session.headers.update({"User-Agent": user_agent})
    auth = OAuth2ClientCredentialsAuth(oauth2client, scope=scope, resource=base_url)
    session = requests.Session()
    session.auth = auth
    # And also later, why not?
    if user_agent is not None:
        session.headers.update({"User-Agent": user_agent})
    return session


def get_biblionumber_marc(session, base_url: str, biblio_id: int) -> dict:
    """Get MARC in JSON data for biblionumber from Koha API

    Args:
    session (oauth2): Oauth2 session provided by `pyreslib.koha.oauth2_session` method.
    biblio_id (int): Biblio ID for the requested record.

    Returns:
    response (dict): MARC in JSON serialization of the record.

    Examples:
    >>> my_session = pyreslib.koha.oauth2_session(client_id="{CLIENT_ID}"", client_secret="{SECRET_KEY}" , base_url="https://{KOHA_STAFF_URL}/api/v1")
    >>> marc_json_record = pyreslib.koha.get_biblionumber_marc(my_session,12)
    """
    headers = {"Accept": "application/marc-in-json"}
    response = session.get(f"{base_url}/biblios/{str(biblio_id)}", headers=headers)
    return response.json()


def get_koopman_keywords(
    record: dict,
    barcode: str,
    koopman_field="653",
    subfields={
        "m_heading": "a",
        "auth_id": "9",
        "pages": "3",
        "barcode": "0",
        "shelfmark": "w",
    },
) -> list:
    """
    Extracts Keywords associated with barcode.
    """
    # get keywords
    koopman_keywords = []
    query_field = list(filter(lambda x: koopman_field in x.keys(), record["fields"]))
    for statement in query_field:
        keyword = {}
        for keyword_key in subfields.keys():
            metadata = list(
                filter(
                    lambda x: subfields[keyword_key] in x.keys(),
                    statement[koopman_field]["subfields"],
                )
            )
            keyword[keyword_key] = metadata[0][subfields[keyword_key]]
        if keyword["barcode"] == barcode:
            koopman_keywords.append(keyword)

    return koopman_keywords


def import_biblionumber_shelfmark_barcode_mapping(mapping_filepath: str) -> list:
    """
    Returns a list of dictionaries based on CSV mapping file
    """
    f = open(mapping_filepath, "r", encoding="utf-8")
    reader = csv.DictReader(
        f, delimiter=";", fieldnames=["biblionumber", "barcode", "call_number"]
    )
    d = {"items": []}
    for row in reader:
        d["items"].append(row)
    biblionumber_mapping = d["items"]
    # extract shelfmark from call_number
    for item in biblionumber_mapping:
        item["shelfmark"] = item["call_number"].split(" ")[-1]

    return biblionumber_mapping


def import_shelfmark_to_barcode_mapping(shelfmark_to_barcode_filepath: str) -> list:
    """
    Returns a list of dictionaries given a CSV file with fields "shelfmark" and "barcode"
    """
    f = open(shelfmark_to_barcode_filepath, "r")
    reader = csv.DictReader(f)
    d = {"items": []}
    for row in reader:
        d["items"].append(row)
    return d["items"]
