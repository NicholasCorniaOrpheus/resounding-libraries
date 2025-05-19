"""Main script for ORCID"""

import sys

sys.path.append("./modules")

from modules.api import *
from modules.utilities import *
from modules.bibtex import *

# print("Importing credentials...")
# credentials = json2dict("../credentials/credentials.json")["orcid"]

# Test

nicholas_orcid = "0000-0003-1114-6710"

# get access token
# access_token = orcid_public_token(credentials)
# nicholas_works = get_works(nicholas_orcid, access_token)

# print("Getting works...")
# output_works_filename = "./data/works/test.json"
# dict2json(nicholas_works, output_works_filename)

# BibTex conversion

bibtex_filename = "./data/works/example.bib"

print("Converting BibTex file into JSON...")
bibtext2json(bibtex_filename)
