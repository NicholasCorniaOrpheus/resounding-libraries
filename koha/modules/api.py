import requests
from requests_oauth2client import OAuth2Client, OAuth2ClientCredentialsAuth
import json
import os

import sys

sys.path.append("./modules")  # importing custom functions in modules

from modules.utilities import *

# Import credentials, assuming you are running the code from the `koha` directory
credentials = json2dict("../credentials/credentials.json")

base_url = credentials["koha"]["koha_api_url"]

oauth_credentials = credentials["koha"]["oauth_credentials"]

basic_credentials = credentials["koha"]["basic_credentials"]


def oauth2_session(client_id, client_secret, base_url, scope="all"):
    token_url = f"{base_url}/oauth/token"  # This may be different for your endpoint

    oauth2client = OAuth2Client(
        token_endpoint=token_url, client_id=client_id, client_secret=client_secret
    )
    auth = OAuth2ClientCredentialsAuth(oauth2client, scope=scope, resource=base_url)
    session = requests.Session()
    session.auth = auth
    return session


def basicAuth():
    # test
    basic = requests.auth.HTTPBasicAuth(
        BasicCredentials["user"], BasicCredentials["password"]
    )
    requests.get(base_url, auth=basic)


# create Oath2 session
my_session = oauth2_session(
    client_id=oauth_credentials["client_id"],
    client_secret=oauth_credentials["secret_key"],
    base_url=base_url,
)


def convert_authority_marc_response(
    response_json, mapping_marc_fields_dict
):  # returns a more readable version of the MARC response of a API query according to a given mapping
    # check authority type
    authority_type = list(
        filter(lambda x: list(x.keys())[0] == "942", response_json["fields"])
    )[0]["942"]["subfields"][0]["a"]
    query = list(
        filter(
            lambda x: x["type"] == authority_type, mapping_marc_fields_dict["authority"]
        )
    )
    if len(query) > 0:
        mapping = query[0]
        # print("Mapping:", mapping)
        pretty_response = {}
        for key in mapping.keys():
            if key != "type":
                pretty_response[key] = {}
                for element in mapping[key]:  # search through all subkeys
                    # print("Element:", element)
                    field_key = list(element.keys())[0]
                    field_number = element[field_key][0]
                    # print("Field to query:", field)
                    query_field = list(
                        filter(
                            lambda x: list(x.keys())[0] == field_number,
                            response_json["fields"],
                        )
                    )

                    subfield_number = element[field_key][1]
                    if subfield_number == "":  # case no subfields, like in auth_id
                        pretty_response[key][field_key] = query_field[0][field_number]
                    else:
                        # consider multiple entries of same field
                        pretty_response[key][field_key] = []
                        for entry in query_field:
                            # search for right subfield
                            query_subfield = list(
                                filter(
                                    lambda x: list(x.keys())[0] == subfield_number,
                                    entry[field_number]["subfields"],
                                )
                            )

                            pretty_response[key][field_key].append(
                                query_subfield[0][subfield_number]
                            )

    else:
        print("Error")
        return {}

    return pretty_response


def get_framework_id_biblioitem(biblio_id):
    # get the JSON response of the biblionumber
    return get_biblionumber_json(biblio_id)["framework_id"]


def get_framework_id_authority(auth_id):
    # get the JSON response of the authority
    return get_authority_json(auth_id)["framework_id"]


def get_authority_json(auth_id):  # returns a JSON response according to Koha fields
    headers = {"Accept": "application/json"}
    response = my_session.get(f"{base_url}/authorities/{str(auth_id)}", headers=headers)
    return response.json()


def get_authority_marc(auth_id):  # returns a JSON response with MARC fields.
    headers = {"Accept": "application/marc-in-json"}
    response = my_session.get(f"{base_url}/authorities/{str(auth_id)}", headers=headers)
    return response.json()


def get_biblionumber_marc(biblio_id):  # returns a JSON response with MARC fields.
    headers = {"Accept": "application/marc-in-json"}
    response = my_session.get(f"{base_url}/biblios/{str(biblio_id)}", headers=headers)
    return response.json()


def put_biblionumber_marc(
    biblio_id, marc_json
):  # updates the metadata of a given biblioitem. The marc_json should be marc-in-json format
    framework_id = get_framework_id_biblioitem(biblio_id)
    if str(framework_id) != "":
        headers = {
            "Accept": "application/json",
            "Content-type": "application/marc-in-json",
            "x-framework-id": str(framework_id),
        }
    else:  # dafault framework
        headers = {
            "Accept": "application/json",
            "Content-type": "application/marc-in-json",
        }
    response = my_session.put(
        f"{base_url}/biblios/{str(biblio_id)}",
        headers=headers,
        data=json.dumps(
            marc_json
        ),  # dumps serializes the Python dictionary into JSON string
    )
    return response.json()


def put_authority_marc(
    auth_id, marc_json
):  # updates the metadata of a given authority. The marc_json should be marc-in-json format
    framework_id = get_framework_id_authority(auth_id)
    if str(framework_id) != "":
        headers = {
            "Accept": "application/json",
            "Content-type": "application/marc-in-json",
            "x-authority-type": str(framework_id),
        }
    else:  # dafault framework
        headers = {
            "Accept": "application/json",
            "Content-type": "application/marc-in-json",
        }
    response = my_session.put(
        f"{base_url}/authorities/{str(auth_id)}",
        headers=headers,
        data=json.dumps(
            marc_json
        ),  # dumps serializes the Python dictionary into JSON string
    )
    return response.json()


def get_biblionumber_json(biblio_id):  # returns a JSON response with MARC fields.
    headers = {"Accept": "application/json"}
    response = my_session.get(f"{base_url}/biblios/{str(biblio_id)}", headers=headers)
    return response.json()


# Unfortunately, MARC-JSON serialization is possible
def get_items_from_biblio_json(
    biblio_id,
):  # returns a JSON response with items as MARC fields.
    headers = {"Accept": "application/json"}
    response = my_session.get(
        f"{base_url}/biblios/{str(biblio_id)}/items", headers=headers
    )
    return response.json()


def put_items_from_biblio_json(
    biblio_id, item_json
):  # updates the metadata of a given biblioitem's items. The item_json should be in json format
    headers = {"Accept": "application/json", "Content-type": "application/json"}
    response = my_session.put(
        f"{base_url}/biblios/{str(biblio_id)}/items",
        headers=headers,
        data=json.dumps(
            item_json
        ),  # dumps serializes the Python dictionary into JSON string
    )
    return response.json()


""" TO DO

- [ ] Create scripts that combines every changes via a dictionary in marc-in-json format.
- [ ] Put biblioitems in batch using Koha API scripts


"""
