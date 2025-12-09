import sys

sys.path.append("./modules")

from modules.utilities import *

from pyzotero import zotero

# Import credentials

credentials = json2dict("../credentials/credentials.json")


def access_zotero_api(client_id, api_key, library_type="user"):
    zot = zotero.Zotero(client_id, library_type, api_key)

    # print first 10 items for testing

    # print(zot.items(limit=10)) works!
