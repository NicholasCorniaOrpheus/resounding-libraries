"""Main script for Koha Research Output FRIS integration with external bibliographic formats."""

import sys

sys.path.append("./modules")

from modules.orcid import *
from modules.utilities import *
from modules.bibtex import *
from modules.csl import *
from modules.zotero import *
from modules.export import *

# Import credentials

credentials = json2dict("../credentials/credentials.json")

""" TO DO:

- Find a way to efficiently extract FRIS research output for each researcher.
    - From cat_dict (fast, but not in real time)
    - Form (private) SQL report
    - From API using JSON query syntax...
- For each research output -> export as BibTex and organize according to name and cluster.


"""


research_groups_file = os.path.join("mappings", "research_groups.json")

bibtext_filepath = os.path.join("data")

entries_mapping = json2dict(os.path.join("mappings", "koha2external_formats.json"))

researchers = generate_researchers_dict(research_groups_file, participant_field="500")


def generate_clusters_bibtext():
    print("Save researchers list in ./mappings/researchers_list.json")

    dict2json(researchers, os.path.join("mappings", "researchers_list.json"))

    print(f"Generating BibTeX entries for researchers...")

    entries = generate_bibtex_entries(
        researchers,
        bibtext_filepath,
        entries_mapping,
        report_id=81,
        fields=["biblio_id", "control", "author", "type"],
    )


def reports_clusters():
    for research_cluster in os.scandir(bibtext_filepath):
        research_cluster_export(research_cluster.path)


### CODE ###

generate_clusters_bibtext()
reports_clusters()
