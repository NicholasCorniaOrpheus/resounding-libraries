"""
Main script
"""

import sys

sys.path.append("./modules")  # importing custom functions in modules
from modules.utilities import *
from modules.report import *
from modules.api import *
from modules.marc import *

# Import credentials, assuming you are running the code from the `koha` directory
credentials = json2dict("../credentials/credentials.json")

# Import and Export folders

biblioitems_marc_dir = os.path.join("data", "biblioitems", "marc")
biblioitems_json_dir = os.path.join("data", "biblioitems", "json")
authorities_marc_dir = os.path.join("data", "authorities", "marc")
authorities_json_dir = os.path.join("data", "authorities", "json")


# TESTING

"""Report test, working!
report_id = 48
report2json(credentials["koha"]["koha_public_report_url"], report_id)
"""

"""API test"""
# print(get_authority_marc(1))

# print(get_biblionumber_marc(1))

"""MARC test"""
# get_last_biblioitems_marc()
