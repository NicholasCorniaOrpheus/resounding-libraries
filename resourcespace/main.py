"""
Main file
"""

import sys

sys.path.append("./modules")

from modules.api import *
from modules.batchimport import *
from modules.koha_metadata import *
from modules.utilities import *

# Import credentials

print("Importing credentials...")
credentials = json2dict("../credentials/credentials.json")["resourcespace"]

# Import local Koha paths

print("Importing catalogue metadata from Koha...")
koha_catalogue_path = "../koha/data/biblioitems/json"

koha_catalogue = import_latest_koha_catalogue_json(koha_catalogue_path)

testing_dir = json2dict("./data/paths.json")["ingestion_path"]

# Mappings

print("Importing RS to Koha mapping...")
rs_fields_mapping = json2dict("./data/field_mapping.json")

# ResourceSpace collection tree
print("Importing RS collection tree from API...")
rs_collection_tree_path = "./data/collections"
rs_main_collection = json2dict("./data/paths.json")["main_collection"]
# add_parent2collection(26, 5, credentials)
rs_collection_tree = import_rs_collection_tree_from_API(
    rs_collection_tree_path, rs_main_collection, credentials
)
# save result into JSON
dict2json(
    rs_collection_tree,
    os.path.join(
        rs_collection_tree_path, "rs_collection_tree-" + get_current_date() + ".json"
    ),
)

# Get new collections from folders
digitization_quality = "In-house low quality"
collection_list = folders2collection_list(testing_dir)
collection_metadata_list = get_collection_metadata_from_koha(
    collection_list, koha_catalogue, rs_fields_mapping, digitization_quality
)
print("Test input:", collection_metadata_list[0])


"""test upload files
resource_id = 22
path = os.path.join(testing_dir, "20129484v18n3", "20129484v18n3_003.jpg")
print(path)
rs_API_cURL_POST(
    credentials,
    query_name="upload_file",
    parameters=[
        str(resource_id),
        "0",
        "0",
        "0",
        path,
    ],
)
"""

# STILL NOT WORKING PROPERLY

create_collections_and_resourcers_from_metadata_list(
    collection_metadata_list,
    rs_collection_tree,
    credentials,
    testing_dir,
    rs_main_collection["resource_type"],
)
