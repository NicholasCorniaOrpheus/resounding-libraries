"""
Main script
"""

import sys

sys.path.append("./modules")  # importing custom functions in modules
from modules.utilities import *
from modules.report import *
from modules.api import *

# Import credentials, assuming you are running the code from the `koha` directory
credentials = json2dict("../credentials/credentials.json")

# TESTING

report_id = 48

report2json(credentials["koha"]["koha_public_report_url"], report_id)
