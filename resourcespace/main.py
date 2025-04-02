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

credentials = json2dict("../credentials/credentials.json")

# Import local Koha paths
koha_catalogue_path = "../koha/data/biblioitems/json"

koha_catalogue = import_latest_koha_catalogue_json(koha_catalogue_path)

testing_dir = "../test/"

# Mappings

rs_fields_mapping = json2dict("./data/field_mapping.json")

"""
TO-DO

- [ x ] match dir_name with barcode from koha_catalogue
- [ x ]extract metadata for resources and place them in resources via field_mapping
- populate rs_collection_tree with collections based on biblioitems and their sub-items:

OI Library
    biblioitem_1
        barcode_1.1
        barcode_1.2
        ...
    ...

"""

# TEST

"""Koha import test: works!"""
digitization_quality = "In-house low quality"
collection_list = folders2collections(testing_dir)
get_collection_metadata_from_koha(
    collection_list, koha_catalogue, rs_fields_mapping, digitization_quality
)


'''API tests
# this one is working great!
# rs_API_cURL_command(credentials["resourcespace"], "get_resource_path", ["10"])
# more complicated one with json arguments as parameter
collection = 22
parent = 5
coldata = (
    """{"allow_changes": 1, "public": 1, "type": 3, "parent":""" + str(parent) + """}"""
)
rs_API_cURL_command(
    credentials["resourcespace"], "save_collection", [str(collection), coldata]
)
'''
