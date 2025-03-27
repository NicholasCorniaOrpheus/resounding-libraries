"""
MARC operations and export using PyMARC
"""
import sys

sys.path.append("./modules")  # importing custom functions in modules
from modules.utilities import *
import os
from copy import deepcopy
from pymarc import MARCReader, Record, Field, Subfield, Indicators

biblioitems_marc = "./data/biblioitems/marc"
authorities_marc = "./data/authorities/marc"


def get_last_marc_file(
    path,
):  # returns the most recent MARC file from the data/biblioitems/marc folder
    return get_latest_file(path)
