"""
Utility fuctions for metadata import from Koha.

We assume that the digitizations are stored locally on a given absolute path stored in `resourcespace/data/ingestion_path.json`

Furthermore, the folders are named according to barcodes, and not biblionumbers.

barcode_x
	- barcode_x_001.jpg
	- barcode_x_002.jpg
	...
barcode_y
	- barcode_y_001.jpg
	- barcode_y_002.jpg
	...


"""

import json
import os

import sys

sys.path.append("./modules")

from modules.api import *
from modules.utilities import *


def import_latest_koha_catalogue_json(koha_catalogue_path):
    print("Getting local JSON pretty serialization of MARC Koha catalogue...")
    return json2dict(get_latest_file(koha_catalogue_path))
