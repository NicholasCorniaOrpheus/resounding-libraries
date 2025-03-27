"""
Main file
"""

import sys

sys.path.append("./modules")

from modules.api import *
from modules.batchimport import *
from modules.utilities import *

# Import credentials

credentials = json2dict("../credentials/credentials.json")


# TEST

"""API tests"""
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
