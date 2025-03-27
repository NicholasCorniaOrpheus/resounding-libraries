import requests
from requests_oauth2client import OAuth2Client, OAuth2ClientCredentialsAuth
import json
import os

base_url = "https://koha.orpheusinstituut.be/api/v1"

# Credentials for Nicholas Cornia
OauthCredentials = {
    "description": "nicholas_cornia",
    "clientID": "303cc27c-aed5-4987-be10-b484a2122723",
    "secretKey": "5b39ae64-b3d5-4b01-b439-92f580c44356",
}

BasicCredentials = {
    "user": "cornia.nicholas@orpheusinstituut.be",
    "password": "koopMan%8899",
}

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


# test basic authorization : Response 200 is positive
# basicAuth()

# create Oath2 session
my_session = oauth2_session(
    client_id=OauthCredentials["clientID"],
    client_secret=OauthCredentials["secretKey"],
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
