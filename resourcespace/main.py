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


"""
TO-DO

- match dir_name with barcode from koha_catalogue
- extract metadata for resources and place them in resources via field_mapping
- populate rs_collection_tree with collections based on biblioitems and their sub-items:

OI Library
    biblioitem_1
        barcode_1.1
        barcode_1.2
        ...
    ...

"""

# TEST

"""Koha import test """


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
