"""
Scripts for importing and working with digital scans.

1. transform pdfs from special collections into jpgs, by renaming the shelfmark into barcode.
2. 

"""
import sys

sys.path.append("./modules")

from modules.utilities import *

import pathlib
import os
import csv
import pdf2image

# Koha API
import requests
from requests_oauth2client import OAuth2Client, OAuth2ClientCredentialsAuth
import json

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
        "keyword": "a",
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


# def shelfmark_to_barcode(shelfmark: str, shelfmark_barcode_mapping: list) -> str:
#     """
#     Given a shelfmark, returns the unique barcode associated to it, based on a mapping.
#     """
#     query_shelfmark = list(
#         filter(lambda x: x["shelfmark"] == shelfmark, shelfmark_barcode_mapping)
#     )

#     if len(query_shelfmark) == 1:
#         # one unique solution
#         barcode = query_shelfmark[0]["barcode"]
#         return barcode
#     elif len(query_shelfmark) > 1:
#         # multiple results
#         print(
#             f"The shelfmark {shelfmark} is associated with multiple barcodes: {query_shelfmark}"
#         )
#         input()
#     else:
#         print(f"Shelfmark {shelfmark} not found.")


def convert_pdfs_to_images(
    directories_path: str,
    output_path: str,
    call_number_barcode_filepath: str,
    convert_shelfmark_to_barcode=True,
):
    """
    Converts a series of PDFs, stored in an arbitrary tree of directories into a series of directories with JPG images.

    Args:
    directories_path (str): parent directory where the PDFs are stored.
    output_path (str): output parent directory for conversion.
    convert_shelfmark_to_barcode (bool): Rename shelfmark in PDF filename to barcode. Default is `True`.

    """
    # get all pdfs in the directory tree
    pdf_files = []
    for f in pathlib.Path(directories_path).rglob("*.pdf"):
        pdf_files.append(f)

    # get call_number-shelfmark mapping
    f = open(call_number_barcode_filepath, "r", encoding="utf-8")
    reader = csv.DictReader(
        f, delimiter=";", fieldnames=["biblionumber", "barcode", "call_number"]
    )
    d = {"items": []}
    for row in reader:
        d["items"].append(row)
    call_number_barcode = d["items"]
    # extract shelfmark from call_number
    for item in call_number_barcode:
        item["shelfmark"] = item["call_number"].split(" ")[-1]

    # extract shelfmark from pdf files
    missing_match = []
    for pdf in pdf_files:
        shelfmark_pdf = pdf.stem.split(" ")[0]
        query_shelfmark = list(
            filter(lambda x: x["shelfmark"] == shelfmark_pdf, call_number_barcode)
        )
        if len(query_shelfmark) == 1:
            barcode = query_shelfmark[0]["barcode"]
            # extract images from pdf path
            images = pdf2image.convert_from_path(pdf)
            # set up output directory
            if os.path.exists(os.path.join(output_path, barcode)):
                pass
            else:
                os.makedirs(os.path.join(output_path, barcode))
            output_dir = os.path.join(output_path, barcode)
            for i in range(len(images)):
                page = str(i + 1)
                images[i].save(
                    os.path.join(output_dir, f"{barcode}_{page.zfill(3)}.jpg"), "JPEG"
                )

            print(f"PDF file {pdf.stem} has been exported!")
        else:
            # append to missing match
            missing_match.append(pdf)
            print(f"Missing: {pdf}")

    print(f"Missing PDFs for matching are {len(missing_match)} \n  {missing_match}")
