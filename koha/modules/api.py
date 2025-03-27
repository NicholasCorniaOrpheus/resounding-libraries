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

# Import mapping
mapping_marc_fields = json2dict("./data/mapping_marc_fields.json")


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
    response_json,
):  # returns a more readable version of the MARC response of a API query according to a given mapping
    # check authority type
    authority_type = list(
        filter(lambda x: list(x.keys())[0] == "942", response_json["fields"])
    )[0]["942"]["subfields"][0]["a"]
    query = list(
        filter(lambda x: x["type"] == authority_type, mapping_marc_fields["authority"])
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


def get_authority_koha(auth_id):  # returns a JSON response according to Koha fields
    headers = {"Accept": "application/json"}
    response = my_session.get(f"{base_url}/authorities/{str(auth_id)}", headers=headers)
    return response.json()


def get_authority_marc(auth_id):  # returns a JSON response with MARC fields.
    headers = {"Accept": "application/marc-in-json"}
    response = my_session.get(f"{base_url}/authorities/{str(auth_id)}", headers=headers)
    return convert_authority_marc_response(response.json())


def get_biblionumber_marc(biblio_id):  # returns a JSON response with MARC fields.
    headers = {"Accept": "application/marc-in-json"}
    response = my_session.get(f"{base_url}/biblios/{str(biblio_id)}", headers=headers)
    return response.json()
