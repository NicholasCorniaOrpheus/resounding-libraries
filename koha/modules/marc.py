"""
MARC operations and export using PyMARC
"""
import sys

sys.path.append("./modules")  # importing custom functions in modules
from modules.utilities import *
import os
from copy import deepcopy
from pymarc import MARCReader, Record, Field, Subfield, Indicators


# returns a more readable version of a MARC dictionary according to a given mapping
def convert_authority_marc_dict(marc_dict, mapping):
    # check authority type
    authority_type = list(
        filter(lambda x: list(x.keys())[0] == "942", marc_dict["fields"])
    )[0]["942"]["subfields"][0]["a"]
    query = list(filter(lambda x: x["type"] == authority_type, mapping))
    if len(query) > 0:
        mapping = query[0]
        # I assume each key has a unique field, with subfields.
        pretty_response = {}
        for key in mapping.keys():
            if key != "type":
                pretty_response[key] = []
                # get associated MARC field to key
                field_key = list(mapping[key][0].keys())[0]
                field_number = mapping[key][0][field_key][0]
                # print("Field to query:", field_number)
                query_field = list(
                    filter(
                        lambda x: list(x.keys())[0] == field_number,
                        marc_dict["fields"],
                    )
                )
                # print(query_field)
                # input()
                # insert multiple entries
                for entry in query_field:
                    pretty_entry = {}
                    # go through every subfield of the key
                    for subfield in mapping[key]:
                        subfiled_key = list(subfield.keys())[0]
                        subfield_number = subfield[subfiled_key][1]
                        # print("Subfield number:", subfield_number)
                        if subfield_number == "":  # case no subfields, like in auth_id
                            pretty_entry[subfiled_key] = query_field[0][field_number]
                        else:
                            # search subfield
                            try:
                                query_subfield = list(
                                    filter(
                                        lambda x: list(x.keys())[0] == subfield_number,
                                        entry[field_number]["subfields"],
                                    )
                                )

                                pretty_entry[subfiled_key] = query_subfield[0][
                                    subfield_number
                                ]

                            except IndexError:
                                pass
                    pretty_response[key].append(pretty_entry)

    else:
        print("Error")
        return {}

    return pretty_response


def auth_marc2json(marc_path, mapping_path, json_path):
    print(f"Getting the latest MARC file of the authorities from {marc_path} ...")
    latest_marc_file = get_latest_file(marc_path)
    print(f"Getting the MARC field mapping from {mapping_path} ...")
    mapping = json2dict(mapping_path)
    # import MARC file using PyMARC
    f = open(latest_marc_file, "rb")
    pretty_records = []
    reader = MARCReader(f)
    print(f"Parsing the MARC records...")
    for record in reader:
        dict_record = record.as_dict()
        pretty_record = convert_authority_marc_dict(dict_record, mapping["authority"])
        pretty_records.append(pretty_record)

    # export pretty record
    print(f"Exporting pretty catalogue in {json_path} ...")
    latest_json_file = os.path.join(
        json_path, os.path.basename(latest_marc_file)[:-4] + ".json"
    )
    print("JSON file save as:", latest_json_file)
    dict2json(pretty_records, latest_json_file)


# returns a more readable version of a MARC dictionary according to a given mapping
def convert_biblioitem_marc_dict(marc_dict, mapping):
    # I assume each key has a unique field, with subfields.
    pretty_response = {}
    for key in mapping.keys():
        if key != "type":
            pretty_response[key] = []
            # get associated MARC field to key
            field_key = list(mapping[key][0].keys())[0]
            field_number = mapping[key][0][field_key][0]
            # print("Field to query:", field_number)
            query_field = list(
                filter(
                    lambda x: list(x.keys())[0] == field_number,
                    marc_dict["fields"],
                )
            )
            # print(query_field)
            # input()
            # insert multiple entries
            for entry in query_field:
                pretty_entry = {}
                # go through every subfield of the key
                for subfield in mapping[key]:
                    subfiled_key = list(subfield.keys())[0]
                    subfield_number = subfield[subfiled_key][1]
                    # print("Subfield number:", subfield_number)
                    if subfield_number == "":  # case no subfields, like in auth_id
                        pretty_entry[subfiled_key] = query_field[0][field_number]
                    else:
                        # search subfield
                        try:
                            query_subfield = list(
                                filter(
                                    lambda x: list(x.keys())[0] == subfield_number,
                                    entry[field_number]["subfields"],
                                )
                            )

                            pretty_entry[subfiled_key] = query_subfield[0][
                                subfield_number
                            ]

                        except IndexError:
                            pass
                pretty_response[key].append(pretty_entry)

    return pretty_response


def biblio_marc2json(marc_path, mapping_path, json_path):
    print(f"Getting the latest MARC file of the catalogue from {marc_path} ...")
    latest_marc_file = get_latest_file(marc_path)
    print(f"Getting the MARC field mapping from {mapping_path} ...")
    mapping = json2dict(mapping_path)
    # import MARC file using PyMARC
    f = open(latest_marc_file, "rb")
    pretty_records = []
    reader = MARCReader(f)
    print(f"Parsing the MARC records...")
    for record in reader:
        dict_record = record.as_dict()
        pretty_record = convert_biblioitem_marc_dict(dict_record, mapping["biblioitem"])
        pretty_records.append(pretty_record)

    # export pretty record
    print(f"Exporting pretty catalogue in {json_path} ...")
    latest_json_file = os.path.join(
        json_path, os.path.basename(latest_marc_file)[:-4] + ".json"
    )
    print("JSON file save as:", latest_json_file)
    dict2json(pretty_records, latest_json_file)
