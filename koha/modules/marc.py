"""
MARC operations and export using PyMARC
"""
import sys

sys.path.append("./modules")  # importing custom functions in modules
from modules.utilities import *
import os
from copy import deepcopy
import re
from pymarc import MARCReader, Record, Field, Subfield, Indicators


def extract_marc_id(records_filename,record_id):
    # setting up output
    output_marc_filename = os.path.join("tmp", f"single_record-{str(record_id)}.mrc")
    output_marc_file = open(output_marc_filename, "wb")
    print(f"Importing {records_filename} as MARC...")
    f = open(records_filename, "rb")
    records_to_be_changed = 0
    reader = MARCReader(f)
    for record in reader:
        current_record_id = str(record["001"])[6:]
        if current_record_id == str(record_id):
            print('Record found. Save mrc file')
            new_record = deepcopy(record)
            output_marc_file.write(new_record.as_marc())
            output_marc_file.close()
            print_mrc_file(output_marc_filename)
            return 



def generate_catalogue_dict(records_filename):
    f = open(records_filename, "rb")
    reader = MARCReader(f)
    catalogue_dict = []
    items_with_no_id = 0
    for record in reader:
        record_dict = record.as_dict()
        try:
            catalogue_dict.append({"biblio_id": record_dict["fields"][0]["001"], "record": record_dict})
        except KeyError:
            items_with_no_id +=1
            pass

    print(f"Number of items with no 001 id field: {items_with_no_id}")

    return catalogue_dict



# Ok
def clean_field_from_catalogue_dict(cat_dict,field_number):
    backup_records = []
    changed_records = []
    # look for records with the given field number
    for record in cat_dict:
        query = list(filter(lambda x: field_number in x.keys(),record["record"]["fields"]) )
        if len(query) >0 : # found items, delete by inverse filtering
            # backup record
            backup_records.append(record)
            # changed record
            changed_record = deepcopy(record)
            changed_record["record"]["fields"] = list(filter(lambda x: field_number not in x.keys(), record["record"]["fields"]))
            changed_records.append(changed_record)


    return backup_records, changed_records


def change_subfield_from_catalogue_dict(cat_dict,filter_field,criterium,change_field,value):
    backup_records = []
    changed_records = []
    # look for records with the given field number
    for record in cat_dict:
        # check filter first
        filter_query = list(filter(lambda x: filter_field[0] in x.keys(),record["record"]["fields"]) )
        meets_criterium = []
        if len(filter_query) >0 :
            for field in filter_query:
                subfields = field[filter_field[0]]["subfields"]
                if all(criterium in subfield[filter_field[1]] for subfield in subfields if filter_field[1] in subfield.keys()):
                    meets_criterium.append(True)
                else:
                    meets_criterium.append(False)

        if False not in meets_criterium:
            change_query = list(filter(lambda x: change_field[0] in x.keys(),record["record"]["fields"]) )
            change_tag = False
            if len(change_query) >0 : # found items
                
                # changed record
                changed_record = deepcopy(record)
                # go through fields to be changed
                for field in changed_record["record"]["fields"]:
                    if change_field[0] in field.keys():
                        subfields = field[change_field[0]]["subfields"]
                        for subfield in subfields:
                            if change_field[1] in subfield.keys():
                                if subfield[change_field[1]] != value:
                                    subfield[change_field[1]] = value
                                    change_tag = True

                if change_tag:
                
                    # changed record
                    changed_records.append(changed_record)

                    # backup record
                    backup_records.append(record)




    return backup_records, changed_records



            
            


            



# clean a specific subfield given a filter criterium.

def clean_field_from_records(field_number, records_filename):  # TESTED, OK
    # setting up output
    output_marc_filename = os.path.join("tmp", "out_clean_field.mrc")
    output_marc_file = open(output_marc_filename, "wb")
    print(f"Importing {records_filename} as MARC...")
    f = open(records_filename, "rb")
    records_to_be_changed = 0
    reader = MARCReader(f)
    for record in reader:
        if len(record.get_fields(field_number)) > 0:
            # print(f"Initial record {record.as_dict()}")
            # print(f"Current biblioitem: {record["001"]}")
            new_record = deepcopy(record)
            records_to_be_changed += 1
            new_record.remove_fields(field_number)
            # write new record as marc
            output_marc_file.write(new_record.as_marc())

    print(f"Number of cleaned records: {records_to_be_changed}")
    # print txt version of new records
    print_mrc_file(output_marc_filename)
    print("Splitting large file")
    split_mrc_file(output_marc_filename, output_marc_filename)

# IMPROVED
def clean_subfield_from_records(
    field_number,
    subfield_key,
    records_filename,
    filter_option,
    filter_field,
    filter_criteria,
):
    # setting up output
    output_marc_filename = os.path.join("tmp", "out_clean_subfield.mrc")
    output_marc_file = open(output_marc_filename, "wb")
    print(f"Importing {records_filename} as MARC...")
    f = open(records_filename, "rb")
    records_to_be_changed = 0
    reader = MARCReader(f)
    items_to_be_processed = []
    if filter_option:  # apply filters
        # get list of items that meet criteria
        for record in reader:
            # print(f"Current record: {record["001"]}")
            filter_fields = record.get_fields(filter_field[0])
            # print(f"Filter fields: {filter_fields}")
            if len(filter_fields) > 0:
                criteria = []
                # make sure all subfields meet the criteria
                for field in filter_fields:
                    subfields = field.get_subfields(filter_field[1])
                    # print(f"Subfields: {subfields}")
                    for subfield in subfields:
                        if any(criterium in subfield for criterium in filter_criteria):
                            criteria.append(True)
                        else:
                            criteria.append(False)
                if False not in criteria:
                    #print(f"item to be processed: {record["001"]} ")
                    items_to_be_processed.append(str(record["001"]))


        print(f"Number of items to be processed for search: {len(items_to_be_processed)}")
        print(items_to_be_processed[0:10])
        # change records
        f.close()
        f = open(records_filename, "rb")
        reader = MARCReader(f)
        for record in reader:
            if str(record["001"]) in items_to_be_processed:
                new_record = deepcopy(record)
                fields_to_be_cleaned = new_record.get_fields(field_number)
                overwrite = False
                for field in fields_to_be_cleaned:
                    if len(field.get_subfields(subfield_key)) > 0:
                        # delete subfield
                        field.delete_subfield(subfield_key)
                        # if field gets empty, delete it from record
                        if str(field)[8:] == "":
                            # print("deleting field...")
                            new_record.remove_field(field)
                        overwrite = True
                if overwrite:
                    print(f"Cleaning {record["001"]}")
                    records_to_be_changed += 1
                    # append new_record to output MARC
                    output_marc_file.write(new_record.as_marc())

            

    else:  # no filter applies
        for record in reader:
            new_record = deepcopy(record)
            fields_to_be_cleaned = new_record.get_fields(field_number)
            if len(fields_to_be_cleaned) > 0:
                overwrite = False
                for field in fields_to_be_cleaned:
                    if len(field.get_subfields(subfield_key)) > 0:
                        # delete subfield
                        field.delete_subfield(subfield_key)
                        # if field gets empty, delete it from record
                        if str(field)[8:] == "":
                            new_record.remove_field(field)
                        overwrite = True
                if overwrite:
                    records_to_be_changed += 1
                    # append new_record to output MARC
                    output_marc_file.write(new_record.as_marc())

            else:
                pass

    print(f"Number of cleaned records: {records_to_be_changed}")
    # print txt version of new records
    print_mrc_file(output_marc_filename)
    print("Splitting large file")
    split_mrc_file(output_marc_filename, output_marc_filename)


def batch_substitute_subfield_from_records(
    field_number,
    subfield_key,
    records_filename,
    value,
    filter_option,
    filter_field,
    filter_criteria,
):

    # setting up output
    output_marc_filename = os.path.join("tmp", "out_clean_subfield.mrc")
    output_marc_file = open(output_marc_filename, "wb")
    print(f"Importing {records_filename} as MARC...")
    f = open(records_filename, "rb")
    records_to_be_changed = 0
    reader = MARCReader(f)
    items_to_be_processed = []
    if filter_option:  # apply filters
        # get list of items that meet criteria
        for record in reader:
            # print(f"Current record: {record["001"]}")
            filter_fields = record.get_fields(filter_field[0])
            # print(f"Filter fields: {filter_fields}")
            if len(filter_fields) > 0:
                criteria = []
                # make sure all subfields meet the criteria
                for field in filter_fields:
                    subfields = field.get_subfields(filter_field[1])
                    # print(f"Subfields: {subfields}")
                    for subfield in subfields:
                        if any(criterium in subfield for criterium in filter_criteria):
                            criteria.append(True)
                        else:
                            criteria.append(False)
                if False not in criteria:
                    #print(f"item to be processed: {record["001"]} ")
                    items_to_be_processed.append(str(record["001"]))


        print(f"Number of items to be processed for search: {len(items_to_be_processed)}")
        print(items_to_be_processed[0:10])
        # change records
        f.close()
        f = open(records_filename, "rb")
        reader = MARCReader(f)
        for record in reader:
            if str(record["001"]) in items_to_be_processed:
                new_record = deepcopy(record)
                fields_to_be_cleaned = record.get_fields(field_number)
                overwrite = False
                for field in fields_to_be_cleaned:
                    if len(field.get_subfields(subfield_key)) > 0:
                        try:
                            if field[subfield_key] != value:
                                field[subfield_key] = value
                                overwrite = True
                        except KeyError:  # no subfield with given key
                            field.add_subfield(subfield_key, value)
                            overwrite = True
                if overwrite:
                    print(f"Processing {record["001"]}")
                    records_to_be_changed += 1
                    # append new_record to output MARC
                    output_marc_file.write(new_record.as_marc())

            

    else:  # no filter applies
        for record in reader:
            new_record = deepcopy(record)
            fields_to_be_cleaned = new_record.get_fields(field_number)
            if len(fields_to_be_cleaned) > 0:
                overwrite = False
                for field in fields_to_be_cleaned:
                    if len(field.get_subfields(subfield_key)) > 0:
                        try:
                            if field[subfield_key] != value:
                                field[subfield_key] = value
                                overwrite = True
                        except KeyError:  # no subfield with given key
                            field.add_subfield(subfield_key, value)
                            overwrite = True
                if overwrite:
                    records_to_be_changed += 1
                    # append new_record to output MARC
                    output_marc_file.write(new_record.as_marc())

            else:
                pass

    print(f"Number of cleaned records: {records_to_be_changed}")
    # print txt version of new records
    print_mrc_file(output_marc_filename)
    print("Splitting large file")
    split_mrc_file(output_marc_filename, output_marc_filename)

def change_leader_from_record(records_filename,leader_position,filter_field,criterium,value,output_name):
    # setting up output
    output_marc_filename = os.path.join("tmp", f"out_change_leader-{output_name}.mrc")
    output_marc_file = open(output_marc_filename, "wb")
    print(f"Importing {records_filename} as MARC...")
    f = open(records_filename, "rb")
    records_to_be_changed = 0
    reader = MARCReader(f)

    for record in reader:
        # get leader value:
        leader = record.leader
        if leader[leader_position] != value:
            if filter_field[0] != "":
                # I assume only one field!
                try:
                    check_criterium = record.get_fields(filter_field[0])[0][filter_field[1]]
                    if criterium in check_criterium:
                        print(f"Current record {record["001"]}")
                        new_record = deepcopy(record)
                        new_record.leader[leader_position] = value 
                        records_to_be_changed += 1
                        # append new_record to output MARC
                        output_marc_file.write(new_record.as_marc())
                except Exception:
                    pass 

            else: # no filtering
                print(f"Current record {record["001"]}")
                new_record = deepcopy(record)
                new_record.leader[leader_position] = value 
                records_to_be_changed += 1
                # append new_record to output MARC
                output_marc_file.write(new_record.as_marc())

        

    print(f"Number of cleaned records: {records_to_be_changed}")
    # print txt version of new records
    print_mrc_file(output_marc_filename)
    print("Splitting large file")
    split_mrc_file(output_marc_filename, output_marc_filename)

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


# extends abbreviations according to ./data/mapping_abbreviation_codes.json
def convert_abbreviations(pretty_record, abbreviation_dict):
    for key in abbreviation_dict.keys():
        if key != "instrumentation":  # instrumentation code has first to be splitted!
            for entry in pretty_record[key]:
                try:
                    entry["code"] = get_abbreviation_code_data(
                        entry["code"], abbreviation_dict[key]
                    )
                except KeyError:
                    pass

        else:  # instrumentation case
            # split instrument string according to spaces and / as alternative instruments
            try:
                multiple_abbr = re.split(" |/", pretty_record[key][0]["code"])
                instruments = []
                for instr_abbr in multiple_abbr:
                    instruments.append(
                        get_abbreviation_code_data(instr_abbr, abbreviation_dict[key])
                    )

                pretty_record[key] = instruments
            except IndexError:
                pass

    return pretty_record


def retrieve_external_source(pretty_record, external_sources_dict):
    for entry in pretty_record["external_sources"]:
        try:
            if entry["source"] == "":
                entry["source"] = get_external_source_authority(
                    entry["url"], external_sources_dict
                )
            else:
                pass
        except KeyError:
            entry["source"] = get_external_source_authority(
                entry["url"], external_sources_dict
            )
    return pretty_record


def biblio_marc2json(
    marc_path, mapping_path, json_path, abbreviation_path, external_source_path
):
    print(f"Getting the latest MARC file of the catalogue from {marc_path} ...")
    latest_marc_file = get_latest_file(marc_path)

    print(f"Getting the MARC field mapping from {mapping_path} ...")
    mapping = json2dict(mapping_path)

    # import abbreviations according to files in data folder
    print(f"Getting the abbreviation code mapping from {abbreviation_path} ...")
    abbreviations_rules = json2dict(abbreviation_path)
    abbreviations = {}
    for rule in abbreviations_rules:
        abbreviations[rule["field_name"]] = json2dict(rule["mapping_path"])

    # import external sources
    print(f"Getting the external sources mapping from {external_source_path} ...")
    external_sources = json2dict(external_source_path)

    # import MARC file using PyMARC
    f = open(latest_marc_file, "rb")
    pretty_records = []
    reader = MARCReader(f)
    print(f"Parsing the MARC records...")
    for record in reader:
        dict_record = record.as_dict()
        pretty_record = convert_biblioitem_marc_dict(dict_record, mapping["biblioitem"])
        # convert abbreviations in record
        # print(pretty_record)
        pretty_record = convert_abbreviations(pretty_record, abbreviations)
        pretty_record = retrieve_external_source(pretty_record, external_sources)
        pretty_records.append(pretty_record)

    # export pretty record
    print(f"Exporting pretty catalogue in {json_path} ...")
    latest_json_file = os.path.join(
        json_path, os.path.basename(latest_marc_file)[:-4] + ".json"
    )
    print("JSON file save as:", latest_json_file)
    dict2json(pretty_records, latest_json_file)
