""" Series of scripts in order to interact witht he Omeka S API and generate specific things"""

import sys

sys.path.append("./modules")  # importing custom functions in modules
from modules.utilities import *

from modules.rdf import *
from modules.api import *

from modules.koha_import import *
from modules.data_validation import *

omeka_api_base_url = "http://192.168.0.7:876/api/"

### Omeka S mappings

mappings_directory = os.path.join("data", "mappings")
# omekas_mapping = generate_omekas_mapping(mappings_directory)

### Credentials

credentials = json2dict("../credentials/credentials.json")

base_url = credentials["koha"]["koha_api_url"]
oauth_credentials = credentials["koha"]["oauth_credentials"]

koha_session = oauth2_session(
    client_id=oauth_credentials["client_id"],
    client_secret=oauth_credentials["client_secret"],
    user_agent=oauth_credentials["user_agent"],
    base_url=base_url,
    scope="all",
)


def import_koha_assets_to_omekas(koha_session, mappings_directory: str):
    """
    1. Get biblionumbers - barcode list from Koha Report as CSV (manually, for now)
    2. Load digitized assets in the import directory (temporary) as folder {barcode} with files {barcode}_{zfill number}.
    3. Generate biblioitems list with marc-in-json metadata from Koha API.
    4. Generate payload according to mappings
    5. Ingest assets to Omeka S (either new item, or update existing)
    6. Generate media payload for each image/asset
    7. Ingest media to Omeka S, linking them to parent item.



    """
    # get biblionumbers-barcode list
    biblionumber_barcode_filepath = os.path.join(
        "data", "mappings", "biblionumber_barcode.csv"
    )
    # load digitized assets
    directories_path = os.path.join("import")
    # generate biblioitems list of record metadata from Koha API
    biblioitems = import_digitized_biblioitems_from_koha_api(
        directories_path, biblionumber_barcode_filepath, koha_session
    )
    # generate mappings
    koha_omekas_mappings = generate_omekas_mapping(mappings_directory)
    # generate payload for each asset

    # import media with payload metadata


#### TEST #####


# get allo items
# data = omekas.get_resources("items")

# update item set to site
# test_change_title(resource_id=4, resource_type="items")
# add_item_set_to_site(resource_id=163, site_id=1)

# get a specific item by id
omeka_id = 175
data = omekas_session.get_resource_by_id(omeka_id, resource_type="items")
print(data)
