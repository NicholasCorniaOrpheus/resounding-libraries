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


"""Given a barcode as entry it will return the biblioitem that has the given input as barcode subitem.

- We assume that the barcode informations in the catalogue are stored in the field `items` with subfield key `barcode`.
You can change these parameters by explicitly changing the `field_key` and `subfield_key` variables.
- Partial matches has to be handled...

"""


def retrieve_biblioitem_from_barcode(
    input_barcode, catalogue_dict, field_key="items", subfield_key="barcode"
):
    for item in catalogue_dict:
        try:
            query = list(
                filter(lambda x: x[subfield_key] == input_barcode, item[field_key])
            )
            if len(query) > 0:
                return item
        except KeyError:  # no barcode in item
            # print("No barcode for item:", item["biblioitem"][0]["id"])
            pass


# Returns a dictionary with field numbers and values, given a biblioitem in Koha format
def biblioitem2rs_metadata(
    biblioitem,
    input_barcode,
    mapping_rs_fields_dict,
    digitization_quality,
    barcode_name="barcode",
    callnumber_name="callnumber",
):
    rs_metadata = {}
    for rs_field in mapping_rs_fields_dict.keys():
        if rs_field in [barcode_name, callnumber_name]:
            koha_field = mapping_rs_fields_dict[rs_field]["koha_field"]
            barcode_subfield = mapping_rs_fields_dict[barcode_name]["koha_subfield"]
            callnumber_subfield = mapping_rs_fields_dict[callnumber_name][
                "koha_subfield"
            ]
            # get only specific callnumber and barcode from items
            filtered_field = list(
                filter(
                    lambda x: x[barcode_name] == input_barcode, biblioitem[koha_field]
                )
            )
            # I assume only one entry
            rs_metadata[barcode_name] = []
            rs_metadata[callnumber_name] = []
            rs_metadata[barcode_name].append(filtered_field[0][barcode_subfield])
            rs_metadata[callnumber_name].append(filtered_field[0][callnumber_subfield])

        else:
            # match field to metadata values in biblioitem
            try:
                koha_field = mapping_rs_fields_dict[rs_field]["koha_field"]
                koha_subfield = mapping_rs_fields_dict[rs_field]["koha_subfield"]
                rs_metadata[rs_field] = []
                for entry in biblioitem[koha_field]:
                    rs_metadata[rs_field].append(entry[koha_subfield])
            except KeyError:  # RS fields not in Koha: digitization quality
                if rs_field == "digitizationquality":
                    rs_metadata[rs_field].append(digitization_quality)
                else:
                    pass

    return rs_metadata
