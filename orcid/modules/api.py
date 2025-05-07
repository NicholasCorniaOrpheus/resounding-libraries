"""Scripts to acces the ORCID API"""

from pyorcid import OrcidAuthentication
from pyorcid import Orcid


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


# Get list of works associated to a given orcid_id
def get_works(orcid_id, access_token):
    # initialize orcid record
    orcid = Orcid(orcid_id=orcid_id, orcid_access_token=access_token, state="public")
    orcid.__dir__()

    # get works
    return orcid.works()
