"""
This script uses BibTex parser library to access and modify BibTex files in Python

Full API:
https://bibtexparser.readthedocs.io/en/main/bibtexparser.html

"""

import sys

sys.path.append("./modules")

from modules.utilities import *

import bibtexparser


def bibtext2json(bibtex_filename):
    # import bibtex
    bibtex_file = open(bibtex_filename, "r")
    library = bibtexparser.load(bibtex_file)
    entries = library.entries

    bibtex_list = []

    for entry in entries:
        print(entry)
        input()
        item = {}
        # read entry keys and record them in the dictionary
        # get fields
        fields = entry.keys()
        for field in fields:
            if field == "ENTRYTYPE":
                item["type"] = entry[field]
            elif field == "ID":
                item["id"] = entry[field]
            else:
                item[field] = entry[field]

        # append entry to list
        bibtex_list.append(item)

    # export to JSON

    dict2json(bibtex_list, bibtex_filename[:-4] + ".json")
