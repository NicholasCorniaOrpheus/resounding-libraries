"""Main script for Koha Research Output FRIS integration with external bibliographic formats."""

import sys

sys.path.append("./modules")

from modules.orcid import *
from modules.utilities import *
from modules.bibtex import *
from modules.csl import *
from modules.zotero import *

# Import credentials

credentials = json2dict("../credentials/credentials.json")

""" TO DO:

- Find a way to efficiently extract FRIS research output for each researcher.
    - From cat_dict (fast, but not in real time)
    - Form (private) SQL report
    - From API using JSON query syntax...
- For each research output -> export as BibTex and organize according to name and cluster.


"""

## TESTING

"""
access_zotero_api(
    credentials["zotero"]["client_id"],
    credentials["zotero"]["client_secret"],
    library_type="user",
)
"""

research_groups_file = os.path.join("data", "mappings", "research_groups.json")

bibtext_filepath = os.path.join("tmp")

entries_mapping = json2dict(
    os.path.join("data", "mappings", "koha2external_formats.json")
)

researchers = generate_researchers_dict(research_groups_file, participant_field="500")

entries = generate_entries(
    researchers,
    bibtext_filepath,
    entries_mapping,
    report_id=81,
    fields=["biblio_id", "control", "author", "type"],
)
