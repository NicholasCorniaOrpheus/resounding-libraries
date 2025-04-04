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

# Mappings

marc2json_mapping = os.path.join("data", "mappings", "mapping_marc_fields.json")
abbreviation_mapping = os.path.join(
    "data", "mappings", "mapping_abbreviation_codes.json"
)
external_sources_mapping = os.path.join(
    "data", "mappings", "mapping_external_sources.json"
)

reports_mapping = os.path.join("data", "mappings", "mapping_reports.json")

# Calling functions

"""TO DO:
- abbreviations2wikidata scripts
- ingestion items script
- make user interface with terminal menu
- make user interface with streamlit...

"""


# TESTING

"""MARC biblio test: works!
biblio_marc2json(
    biblioitems_marc_dir,
    marc2json_mapping,
    biblioitems_json_dir,
    abbreviation_mapping,
    external_sources_mapping,
)
"""
report_id = 73
personal_names2rs_dynamiclist(
    credentials["koha"]["koha_public_report_url"], reports_mapping, report_id
)

"""Report test, working!
report_id = 71
report2json(credentials["koha"]["koha_public_report_url"],reports_mapping, report_id)
"""

# report_id = 71
# koha_biblioitems2json(credentials["koha"]["koha_public_report_url"],reports_mapping, report_id)

"""API test"""
# print(get_authority_marc(1))

# print(get_biblionumber_marc(1))


"""MARC auth test"""
# auth_marc2json(authorities_marc_dir, marc2json_mapping, authorities_json_dir)
