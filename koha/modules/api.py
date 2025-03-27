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

fields = {"biblioitems": "biblios"}


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
    client_id=OauthCredentials["client_id"],
    client_secret=OauthCredentials["secret_key"],
    base_url=base_url,
)

# Testing API with Oauth
# FULL MARC RECORD
# headers = {"Accept": "application/marc-in-json"}
# Only Koha Database parameters
headers = {"Accept": "application/json"}

query_parameters = {"author": {"-like": "Jean%"}}

# query_parameters = {}

# get authority by id
auth_id = 1
response = my_session.get(f"{base_url}/authorities/{auth_id}", headers=headers)
# print(response.json())
# get biblionumber by id
biblio_id = 1
response = my_session.get(f"{base_url}/biblios/{auth_id}", headers=headers)
print(response.json())

# filter biblios based on author NOT WORKING
response = my_session.get(
    f"{base_url}/biblios", headers=headers, params=query_parameters
)
print("Request URL: ", response.url)
print("Response: \n", response.json())
