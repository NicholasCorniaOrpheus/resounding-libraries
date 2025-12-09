"""
Main script
"""

import sys

sys.path.append("./modules")  # importing custom functions in modules
from modules.utilities import *
from modules.report import *
from modules.api import *
from modules.marc import *
from modules.koopman import *
from modules.digitized_material import *

# Import credentials, assuming you are running the code from the `koha` directory
credentials = json2dict("../credentials/credentials.json")

# Import and Export folders

biblioitems_marc_dir = os.path.join("data", "biblioitems", "marc")
biblioitems_json_dir = os.path.join("data", "biblioitems", "json")
authorities_marc_dir = os.path.join("data", "authorities", "marc")
authorities_json_dir = os.path.join("data", "authorities", "json")

batch_modifications_dir = os.path.join("data", "api_responses", "batch_modifications")


# Mappings

marc2json_mapping = os.path.join("data", "mappings", "mapping_marc_fields.json")
abbreviation_mapping = os.path.join(
    "data", "mappings", "mapping_abbreviation_codes.json"
)
external_sources_mapping = os.path.join(
    "data", "mappings", "mapping_external_sources.json"
)

reports_mapping = os.path.join("data", "mappings", "mapping_reports.json")

items_json_marc_mapping = csv2dict(
    os.path.join("data", "mappings", "mapping_api_item_marc_json.csv")
)


def export_biblioitems_and_authorities():
    print("Exporting biblioitems and authorities from MARC to JSON...")
    biblio_marc2json(
        biblioitems_marc_dir,
        marc2json_mapping,
        biblioitems_json_dir,
        abbreviation_mapping,
        external_sources_mapping,
    )
    auth_marc2json(authorities_marc_dir, marc2json_mapping, authorities_json_dir)


def special_collection_report(source_of_acquisition, exclude_section):
    print("Generate Special collection report")
    special_collection2csv(
        biblioitems_json_dir,
        os.path.join("data", "koopman"),
        source_of_acquisition=source_of_acquisition,
        exclude_section=exclude_section,
    )


def add_reproduction_note_digitized_material():
    print("Adding reproduction note to digitized material...")
    digitized_barcodes_list_filepath = os.path.join(
        "data", "digitized_material", "iGuana_2025_list.csv"
    )

    biblioitems_marc_filepath = get_latest_file(
        os.path.join("data", "biblioitems", "marc")
    )

    f = open(biblioitems_marc_filepath, "rb")

    reader = MARCReader(f)

    digitized_records_filepath = os.path.join(
        "data", "digitized_material", "digitization_iGuana2025.mrc"
    )

    digitized_barcodes_dict = csv2dict(digitized_barcodes_list_filepath)

    digitized_barcodes_list = [entry["barcode"] for entry in digitized_barcodes_dict]

    note = "Digitized by iGuana, Spring 2025."
    reproduction_note_tag2marc(
        reader, digitized_records_filepath, digitized_barcodes_list, note
    )
    print(f"Digitized records MARC file saved as {digitized_records_filepath}")


### CODE ###

# clean inventory number in old collection

# substitute data acquisition for books with Source of acquisition = "Koopman"


def substitute_date_acquisition_Koopman():
    print("Substitute data acquisition for books with Source of acquisition = Koopman")
    batch_substitute_subfield_from_records(
        "952",
        "d",
        get_latest_file(biblioitems_marc_dir),
        "2020-07-08",
        filter_option=True,
        filter_field=["952", "e"],
        filter_criteria=["Koopman"],
    )


def remove_inventory_number_from_cells():
    # remove inventory number if record is in Cells
    print("Remove inventory number if record is in Cells")
    clean_subfield_from_records(
        "952",
        "i",
        get_latest_file(biblioitems_marc_dir),
        filter_option=True,
        filter_field=["952", "o"],
        filter_criteria=["KTS1 C1", "KTS1 C2", "KTS1 C3"],
    )



def clean_field_336_cat_dict():
    backup_records, changed_records = clean_field_from_catalogue_dict(cat_dict, "336")

    print(f"Number of records to be changed: {len(changed_records)}")

    # save backup of original records

    backup_filename = os.path.join(
        batch_modifications_dir,
        "backup",
        "backup_records_336-" + get_current_date() + ".json",
    )

    dict2json(backup_records, backup_filename)

    changed_filename = os.path.join(
        batch_modifications_dir,
        "changed",
        "changed_records_336-" + get_current_date() + ".json",
    )

    dict2json(changed_records, changed_filename)

    return backup_records, changed_records


def change_subfield_date_acquisiton_koopman():
    print("Change field 952$d to 2020-07-08 if field 952$e = Koopman")

    backup_records, changed_records = change_subfield_from_catalogue_dict(
        cat_dict,
        filter_field=["952", "e"],
        criterium="Koopman",
        change_field=["952", "d"],
        value="2020-07-08",
    )

    print(f"Number of records to be changed: {len(changed_records)}")

    # save backup of original records

    backup_filename = os.path.join(
        batch_modifications_dir,
        "backup",
        "backup_records_952d-" + get_current_date() + ".json",
    )

    dict2json(backup_records, backup_filename)

    changed_filename = os.path.join(
        batch_modifications_dir,
        "changed",
        "changed_records_952d-" + get_current_date() + ".json",
    )

    dict2json(changed_records, changed_filename)

    return backup_records, changed_records

def change_leader6_if_material_type_score():
    backup_records, changed_records, problematic_leaders = update_leader_from_catalogue_dict(cat_dict,filter_field=["942","c"],criterium="SCO",leader_position=6,value="c")

    print(f"Number of records to be changed: {len(changed_records)}")

    # save backup of original records

    backup_filename = os.path.join(
        batch_modifications_dir,
        "backup",
        "backup_records_leader6_942$c_SCO-" + get_current_date() + ".json",
    )

    dict2json(backup_records, backup_filename)

    changed_filename = os.path.join(
        batch_modifications_dir,
        "changed",
        "changed_records_leader6_942$c_SCO-" + get_current_date() + ".json",
    )

    dict2json(changed_records, changed_filename)

    problematic_leaders_filename = os.path.join(batch_modifications_dir,"problematic_leaders", "problematic_leaders_leader6_942$c_SCO-" + get_current_date() + ".csv")

    dict2csv(problematic_leaders, problematic_leaders_filename)
    
    return backup_records, changed_records

def change_leader6_if_material_type_book():
    backup_records, changed_records, problematic_leaders = update_leader_from_catalogue_dict(cat_dict,filter_field=["942","c"],criterium="BOO",leader_position=6,value="a")

    print(f"Number of records to be changed: {len(changed_records)}")

    # save backup of original records

    backup_filename = os.path.join(
        batch_modifications_dir,
        "backup",
        "backup_records_leader6_942$c_BOO-" + get_current_date() + ".json",
    )

    dict2json(backup_records, backup_filename)

    changed_filename = os.path.join(
        batch_modifications_dir,
        "changed",
        "changed_records_leader6_942$c_BOO-" + get_current_date() + ".json",
    )

    dict2json(changed_records, changed_filename)

    problematic_leaders_filename = os.path.join(batch_modifications_dir,"problematic_leaders", "problematic_leaders_leader6_942$c_BOO-" + get_current_date() + ".csv")

    dict2csv(problematic_leaders, problematic_leaders_filename)
    
    return backup_records, changed_records

def change_leader7_if_cells():
    backup_records, changed_records, problematic_leaders = update_leader_from_catalogue_dict(cat_dict,filter_field=["952","o"],criterium="KTS1 C",leader_position=7,value="m")

    print(f"Number of records to be changed: {len(changed_records)}")

    # save backup of original records

    backup_filename = os.path.join(
        batch_modifications_dir,
        "backup",
        "backup_records_leader7_952$o_KTS1_C-" + get_current_date() + ".json",
    )

    dict2json(backup_records, backup_filename)

    changed_filename = os.path.join(
        batch_modifications_dir,
        "changed",
        "changed_records_leader7_952$o_KTS1_C-" + get_current_date() + ".json",
    )

    dict2json(changed_records, changed_filename)

    problematic_leaders_filename = os.path.join(batch_modifications_dir,"problematic_leaders", "problematic_leaders_leader7_952$o_KTS1_C-" + get_current_date() + ".csv")

    dict2csv(problematic_leaders, problematic_leaders_filename)
    
    return backup_records, changed_records

# NOT WORKING, the pyMARC function leader() cannot handle badly formatted leaders correctly.
def update_problematic_leaders():

    """
    problematic_leaders = csv2dict(
        get_latest_file(os.path.join(batch_modifications_dir, "problematic_leaders"))
    )
    """
    print(f"Importing problematic leaders CSV {os.path.join(batch_modifications_dir, "problematic_leaders", "problematic_leaders_leader7_952$o_KTS1_C-2025-12-05.csv")}")
    problematic_leaders = csv2dict(os.path.join(batch_modifications_dir, "problematic_leaders", "problematic_leaders_leader7_952$o_KTS1_C-2025-12-05.csv"))


    print("Updating problematic leaders via Koha API...")

    problematic_leaders_to_marc(get_latest_file(biblioitems_marc_dir),problematic_leaders,leader_position=7,value="m")




def restore_backup_records_via_koha_api():
    print("Restoring backup records via Koha API...")
    num_changes = len(backup_records)
    i = 1
    for record in enumerate(backup_records):
        print(f"Restoring biblioitem: {record[1]['biblio_id']}")
        # items version
        items = get_items_from_biblio_json(record[1]["biblio_id"])
        # put items back
        new_items = []
        backup_items = list(
            filter(
                lambda x: "952" in x.keys(), backup_records[record[0]]["record"]["fields"]
            )
        )
        for item in enumerate(items):
            new_items.append({})
            for prop in item[1].keys():
                query_prop = list(
                    filter(
                        lambda x: x["json_property"] == prop, items_json_marc_mapping
                    )
                )
                if len(query_prop) > 0:
                    marc_field = query_prop[0]["field"]
                    marc_subfield = query_prop[0]["subfield"]
                    # get new value from changed record
                    new_value = list(
                        filter(
                            lambda x: marc_subfield in x.keys(),
                            backup_items[item[0]]["952"]["subfields"],
                        )
                    )
                    try:
                        new_items[item[0]][prop] = new_value[0][marc_subfield]
                    except IndexError:
                        print(f"No new value for item {item[0]} property {prop}")




        # putting modified items in record via API
        print(put_items_from_biblio_json(record[1]["biblio_id"],new_items))

        # record version
        #print(put_biblionumber_marc(record[1]["biblio_id"], record[1]["record"]))
        print(f"Progress: {i} / {num_changes}")
        i += 1

def put_changes_via_koha_api(change_items,change_records):
    print("Applying changes via Koha API...")
    num_changes = len(changed_records)

    # special handling for items
    if change_items:
        print("Changing items...")
        i = 1
        for record in enumerate(changed_records):
            print(f"Current biblioitem: {record[1]["biblio_id"]}")
            # check if items have been changed
            backup_items = list(
                filter(
                    lambda x: "952" in x.keys(), backup_records[record[0]]["record"]["fields"]
                )
            )
            changed_items = list(
                filter(lambda x: "952" in x.keys(), record[1]["record"]["fields"])
            )

            if backup_items != changed_items:
                #print(f"Items changed for biblio_id {record[1]['biblio_id']}")
                items = get_items_from_biblio_json(record[1]["biblio_id"])
                #print(f"Old items: {items}")
                # PUT only the necessary fields, all the rest causes 500 error in server!
                new_items = []
                for item in enumerate(items):
                    new_items.append({})
                    for prop in item[1].keys():
                        query_prop = list(
                            filter(
                                lambda x: x["json_property"] == prop, items_json_marc_mapping
                            )
                        )
                        if len(query_prop) > 0:
                            marc_field = query_prop[0]["field"]
                            marc_subfield = query_prop[0]["subfield"]
                            # get new value from changed record
                            new_value = list(
                                filter(
                                    lambda x: marc_subfield in x.keys(),
                                    changed_items[item[0]]["952"]["subfields"],
                                )
                            )
                            try:
                                new_items[item[0]][prop] = new_value[0][marc_subfield]
                            except IndexError:
                                print(f"No new value for item {item[0]} property {prop}")




                # putting modified items in record via API
                put_items_from_biblio_json(record[1]["biblio_id"],new_items)
                #input()

            print(f"Progress: {i} / {num_changes}")
            i += 1 

    
    if change_records:
        # changing biblioitem values
        i = 1
        print("Changing records...")
        for record in enumerate(changed_records):
            print(f"Current biblioitem: {record[1]['biblio_id']}")
            # PUT modified record via API

            put_biblionumber_marc(record[1]["biblio_id"], record[1]["record"])
            #input()

            print(f"Progress: {i} / {num_changes}")
            i += 1    

def get_latest_changed_records():
    backup_records = json2dict(
        get_latest_file(os.path.join(batch_modifications_dir, "backup"))
    )

    changed_records = json2dict(
        get_latest_file(os.path.join(batch_modifications_dir, "changed"))
    )

    return backup_records, changed_records


### CODE ###

print(get_biblionumber_marc(22713))
input()

print("Would you like to import a new catalogue dictionary? y/n")

answer = input()

if answer == "y":
    print(f"Importing catalogue from {get_latest_file(biblioitems_marc_dir)}")

    cat_dict = generate_catalogue_dict(get_latest_file(biblioitems_marc_dir))

    dict2json(
        cat_dict,
        os.path.join(
            batch_modifications_dir,"cat_dict", "cat_dict-" + get_current_date() + ".json"
        ),
    )

else:
    print(
        f"Importing last catalogue dictionary from {get_latest_file(os.path.join(batch_modifications_dir,"cat_dict"))}"
    )

    cat_dict = json2dict(
        get_latest_file(os.path.join(batch_modifications_dir, "cat_dict"))
    )

# cleaning script

# backup_records, changed_records = clean_field_336_cat_dict()

#backup_records, changed_records = change_subfield_date_acquisiton_koopman()

#backup_records, changed_records = get_latest_changed_records()

#backup_records, changed_records = change_leader6_if_material_type_score()

#backup_records, changed_records = change_leader6_if_material_type_book()

#backup_records, change_records = change_leader7_if_cells()

# leader scripts

update_problematic_leaders()

# apply changes via Koha API

#restore_backup_records_via_koha_api()

#put_changes_via_koha_api(change_items=False,change_records=True)






# the API format marc-in-JSON is identical to record.as_marc()

# Reinsert metadata in case of errors:
# extract_marc_id(get_latest_file(biblioitems_marc_dir), 3)

# Try to update the record directly via API!
# marc_json = get_biblionumber_marc(3)
# print(marc_json)
# input()
# print(put_biblionumber_marc(3, marc_json))

# auth_marc = get_authority_marc(39271)
# auth_json = get_authority_json(39271)
# print(get_framework_id_authority(39271))

# print(put_authority_marc(39271, auth_marc))


# print(get_framework_id_biblioitem(3))

"""
# If Material type = Score -> leader[6]=c
change_leader_from_record(
    get_latest_file(biblioitems_marc_dir),
    leader_position=6,
    filter_field=["942", "c"],
    criterium="SCO",
    value="c",
    output_name="SCO_to_leader6_c",
)

# If material type = book -> leader[6]=a
change_leader_from_record(
    get_latest_file(biblioitems_marc_dir),
    leader_position=6,
    filter_field=["942", "c"],
    criterium="BOO",
    value="a",
    output_name="BOO_to_leader6_a",
)

# If item in cells -> leader[7]=m
change_leader_from_record(
    get_latest_file(biblioitems_marc_dir),
    leader_position=6,
    filter_field=["952", "o"],
    criterium="KTS1 C",
    value="a",
    output_name="Cellen_to_leader7_m",
)

"""
