import sys

sys.path.append("./modules")

from modules.utilities import *

from pyorcid import OrcidAuthentication
from pyorcid import Orcid
from pyorcid import OrcidSearch

# Import credentials

credentials = json2dict("../credentials/credentials.json")


# Gets access token via credentials
def orcid_public_token(credentials):
    """Get the public token from ORCID"""
    # Create an instance of OrcidAuthentication
    auth = OrcidAuthentication(
        client_id=credentials["client_id"],
        client_secret=credentials["client_secret"],
        redirect_uri=credentials["redirect_uri"],
    )

    # Get the public token
    public_token = auth.get_public_access_token()

    return public_token


access_token = orcid_public_token(credentials["orcid"])


def get_orcid_id_from_name(
    name,
    access_token=access_token,
    base_email="orpheusinstituut.be",
    institutions=["Orpheus Institute", "Orpheus Instituut"],
):
    # initialize orcid record
    orcidSearch = OrcidSearch(orcid_access_token=access_token, state="public")

    search_result = orcidSearch.search(name, rows=10)["expanded-result"]

    email_filter = []

    for person in search_result:
        for email in person["email"]:
            if base_email in email:
                return person["orcid-id"]
            for institution in person["institution-name"]:
                if institution in institutions:
                    return person["orcid-id"]

    print(f"No ORCID found with. Take the first result")
    print(search_result[0])
    print("Save orcid? y/n")
    answer = input()
    if answer == "y":
        return search_result[0]["orcid-id"]


# Get list of works associated to a given orcid_id
def get_works(orcid_id, access_token=access_token):
    # initialize orcid record
    orcid = Orcid(orcid_id=orcid_id, orcid_access_token=access_token, state="public")
    orcid.__dir__()

    # get works
    return orcid.works()
