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

reports_url = credentials["koha"]["koha_reports_url"]

public_reports_url = credentials["koha"]["koha_public_report_url"]

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
        basic_credentials["user"], basic_credentials["password"]
    )
    requests.get(base_url, auth=basic)


# create Oath2 session
my_session = oauth2_session(
    client_id=oauth_credentials["client_id"],
    client_secret=oauth_credentials["secret_key"],
    base_url=base_url,
)





def get_biblionumber_marc(biblio_id):  # returns a JSON response with MARC fields.
    headers = {"Accept": "application/marc-in-json"}
    response = my_session.get(f"{base_url}/biblios/{str(biblio_id)}", headers=headers)
    return response.json()


def get_authority_marc(auth_id):  # returns a JSON response with MARC fields.
    headers = {"Accept": "application/marc-in-json"}
    response = my_session.get(f"{base_url}/authorities/{str(auth_id)}", headers=headers)
    return response.json()

def get_public_report(report_id,fields):
    response = requests.get(f"{public_reports_url}{str(report_id)}")
    """
    print("REQUEST URL:", response.request.url)
    print("REQUEST HEADERS:", response.request.headers)
    print("REQUEST BODY (bytes):", response.request.body)
    print("STATUS:", response.status_code)
    print("RESPONSE HEADERS:", response.headers)
    print("RESPONSE TEXT (truncated):", (response.text or "")[:1000])
    input()
    """
    raw_response = response.json()
    pretty_response = []
    for item in raw_response:
        pretty_response.append({})
        for i in range(len(fields)):
            pretty_response[-1][fields[i]] = item[i]

    return pretty_response





# NOT WORKING, PROBLEM WITH AUTHENTICATION
def get_private_report(report_id):
    headers = {"Accept": "application/json"}
    #url_report = f"{reports_url}{str(report_id)}?login_userid={basic_credentials["user"]}&login_password={basic_credentials["password"]}"
    user_and_pass = f"userid={basic_credentials["user"]}&password={basic_credentials["password"]}"

    report_session = requests.Session()
    response = report_session.get(f"https://koha.orpheusinstituut.be/cgi-bin/koha/svc/authentication",data=user_and_pass)

    print("REQUEST URL:", response.request.url)
    print("REQUEST HEADERS:", response.request.headers)
    print("REQUEST BODY (bytes):", response.request.body)
    print("STATUS:", response.status_code)
    print("RESPONSE HEADERS:", response.headers)
    print("RESPONSE TEXT (truncated):", (response.text or "")[:1000])
    input()

    url_report = f"{reports_url}{report_id}"

    #basic_auth_token = report_session.get(f"https://koha.orpheusinstituut.be/cgi-bin/koha/svc/authentication",data=user_and_pass)
    #print(basic_auth_token)
    response = report_session.get(url_report, headers=headers,  timeout=30)
    # Debugging
    print("REQUEST URL:", response.request.url)
    print("REQUEST HEADERS:", response.request.headers)
    print("REQUEST BODY (bytes):", response.request.body)
    print("STATUS:", response.status_code)
    print("RESPONSE HEADERS:", response.headers)
    print("RESPONSE TEXT (truncated):", (response.text or "")[:1000])
    input()

    return response.json()
