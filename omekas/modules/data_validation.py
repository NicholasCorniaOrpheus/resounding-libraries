# Scripts for validating data after bulk imports

import sys

sys.path.append("./modules")  # importing custom functions in modules
from modules.utilities import *
from modules.api import *


def convert_textual_dates_to_timestamps(item, omekas_mapping):
    # TO BE CONTINUED

    """Example with date
        Good version:
        'dcterms:date': [{'type': 'numeric:timestamp', 'property_id': 7, 'property_label': 'Date', 'is_public': True, '@value': '2025-11-28', '@type': 'http://www.w3.org/2001/XMLSchema#date'}]
    Bad version:
        'dcterms:date': [{'type': 'literal', 'property_id': 7, 'property_label': 'Date', 'is_public': True, '@value': '2025-11-28'}]

    """

    return None
