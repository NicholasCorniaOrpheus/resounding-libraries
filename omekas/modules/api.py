# Omeka S Tools

import sys

sys.path.append("./modules")  # importing custom functions in modules
from modules.utilities import *

from omeka_s_tools.api import OmekaAPIClient
import requests


# Import credentials, assuming you are running the code from the `koha` directory
credentials = json2dict("../credentials/credentials.json")

omeka_credentials = {
    "api_url": credentials["omekas"]["api_url"],
    "key_identity": credentials["omekas"]["key_identity"],
    "key_credential": credentials["omekas"]["key_credential"],
}


# Initialize Client
omekas = OmekaAPIClient(
    api_url=omeka_credentials["api_url"],
    key_identity=omeka_credentials["key_identity"],
    key_credential=omeka_credentials["key_credential"],
)
