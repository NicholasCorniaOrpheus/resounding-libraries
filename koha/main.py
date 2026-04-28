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
from modules.wikidata import *
from modules.isbn import *


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

external_ids_mapping = json2dict(os.path.join("data", "mappings", "mapping_external_ids.json"))

reports_mapping = os.path.join("data", "mappings", "mapping_reports.json")

items_json_marc_mapping = csv2dict(
    os.path.join("data", "mappings", "mapping_api_item_marc_json.csv")
)

wikidata_koha_properties_mapping = csv2dict(os.path.join("data","mappings","wikidata-koha-properties.csv"))


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
def update_problematic_leaders(prob_leaders_filename,leader_position,value):

    """
    problematic_leaders = csv2dict(
        get_latest_file(os.path.join(batch_modifications_dir, "problematic_leaders"))
    )
    """
    print(f"Importing problematic leaders CSV {os.path.join(batch_modifications_dir, "problematic_leaders", prob_leaders_filename)}")
    problematic_leaders = csv2dict(os.path.join(batch_modifications_dir, "problematic_leaders", prob_leaders_filename))


    print("Updating problematic leaders...")

    problematic_leaders_to_marc(get_latest_file(biblioitems_marc_dir),problematic_leaders,leader_position=leader_position,value=value)




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
            input()

            print(get_biblionumber_marc(record[1]["biblio_id"]))

            print(f"Progress: {i} / {num_changes}")
            i += 1   

def put_changes_authorities_via_koha_api(changed_authorities):
    print("Applying changes via Koha API...")
    num_changes = len(changed_authorities)

    i = 1
    print("Changing authorities...")

    print("Would you like to recover an interrupted pull? (y/n)")
    answer = input()
    if  answer == "y":
        start_auth = int(input("Provide the auth_id where you wish to recover the pull:"))
    else:
        start_auth = 0

    for auth in changed_authorities:
        if int(auth["auth_id"]) >= start_auth:
            print(f"Current auth_id: {auth["auth_id"]}")
            # PUT modified record via API
            if i <= 5:
                put_authority_marc(auth["auth_id"], auth["record"])
                input()

                print(get_authority_marc(auth["auth_id"]))
            else:
                put_authority_marc(auth["auth_id"], auth["record"])

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

def import_cat_dict():
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

        return cat_dict

    else:
        print(
            f"Importing last catalogue dictionary from {get_latest_file(os.path.join(batch_modifications_dir,"cat_dict"))}"
        )

        cat_dict = json2dict(
            get_latest_file(os.path.join(batch_modifications_dir, "cat_dict"))
        )

        return cat_dict

def import_auth_dict():
    print("Would you like to import a new authority dictionary? y/n")

    answer = input()

    if answer == "y":

        print("1. From local MARC backup file. 2. From API):")
        answer = int(input())
        if answer == 1:
            print(f"Importing authorities from {get_latest_file(authorities_marc_dir)}")

            auth_dict = generate_authority_dict_from_marc(get_latest_file(authorities_marc_dir))
        elif answer == 2:
            start_time = time()
            print("Importing authorities from API...")
            auth_dict = generate_authority_dict_from_api_parallel(mapping_reports_path=reports_mapping,report_id=84, public_report_url=credentials["koha"]["koha_public_report_url"])
            print(f"Authorities imported in {float(time() - start_time)/60} minutes")

        dict2json(
            auth_dict,
            os.path.join(
                batch_modifications_dir,"auth_dict", "auth_dict-" + get_current_date() + ".json"
            ),
        )

        return auth_dict

    else:
        print(
            f"Importing last authority dictionary from {get_latest_file(os.path.join(batch_modifications_dir,"auth_dict"))}"
        )

        auth_dict = json2dict(
            get_latest_file(os.path.join(batch_modifications_dir, "auth_dict"))
        )

        return auth_dict

def fix_missing_9_subfield_in_authorities(auth_dict):

    backup_authorities, changed_authorities = add_auth_id_in_authority_field(auth_dict)

    # save backup of original records

    backup_filename = os.path.join(
        batch_modifications_dir,
        "backup",
        "backup_fix_subfield_9-" + get_current_date() + ".json",
    )

    dict2json(backup_authorities, backup_filename)

    changed_filename = os.path.join(
        batch_modifications_dir,
        "changed",
        "changed_fix_subfield_9-" + get_current_date() + ".json",
    )

    dict2json(changed_authorities, changed_filename)

    print(f"Number of authorities to be changed: {len(changed_authorities)}")

    print("Putting changes via API...")

    put_changes_authorities_via_koha_api(changed_authorities)

def wikidata_enhancing(auth_dict,in_progress):

    qid_log_dir = os.path.join("data","wikidata")

    wikidata_koha_mapping = csv2dict(os.path.join("data","mappings","wikidata-koha-properties.csv"))

    print(f"Number of authorities: {len(auth_dict)}")

    backup_authorities, changed_authorities = enhance_authorities_via_wikidata(auth_dict,qid_log_dir,wikidata_koha_mapping,batch_modifications_dir,in_progress=in_progress)

    # Saving to JSON...
    dict2json(
        backup_authorities,
        os.path.join(
            batch_modifications_dir,"backup", "backup_authorities_wikidata-" + get_current_date() + ".json"
        ),
    )
    dict2json(
        changed_authorities,
        os.path.join(
            batch_modifications_dir,"changed", "changed_authorities_wikidata-" + get_current_date() + ".json"
        ),
    )

    print(f"Backup and changed records JSON saved. Have a look at them before pushing the changes via API.")

    input()

    generate_authorities_wikidata_statistics()

    put_changes_authorities_via_koha_api(changed_authorities)

def generate_authorities_wikidata_statistics():
    #Import latest changed json file
    latest_changed_authorities_filepath = get_latest_file(os.path.join(batch_modifications_dir,"changed"))
    print(f"Getting latest changed authorities file {latest_changed_authorities_filepath}...")
    changed_authorities = json2dict(latest_changed_authorities_filepath)
    statistics = generate_statistics_authorities_wikidata_enhancement(changed_authorities,wikidata_koha_properties_mapping)

    # save to JSON
    statistic_filepath = f"{latest_changed_authorities_filepath.split(".")[0]}_statistics.json"
    print(f"Saving statistics in {statistic_filepath}...")
    dict2json(statistics,statistic_filepath)

def external_sources_labels(auth_dict):
    print("Adding external identifier metadata to authorities...")
    backup_authorities, changed_authorities = external_sources_metadata_authorities(auth_dict,external_ids_mapping)

    print(f"Number of changes: {len(changed_authorities)}")

    # Saving to JSON...
    dict2json(
        backup_authorities,
        os.path.join(
            batch_modifications_dir,"backup", "backup_authorities_external_ids-" + get_current_date() + ".json"
        ),
    )
    dict2json(
        changed_authorities,
        os.path.join(
            batch_modifications_dir,"changed", "changed_authorities_external_ids-" + get_current_date() + ".json"
        ),
    )

    print(f"Backup and changed records JSON saved. Have a look at them before pushing the changes via API.")

    input()

    put_changes_authorities_via_koha_api(changed_authorities)

# TESTED. It works nicely.
def cleanup_main_headings(auth_dict):

    backup_authorities, changed_authorities = cleanup_parenthesis_location_from_main_heading(
        auth_dict,wikidata_koha_properties_mapping,batch_modifications_dir)

    # Saving to JSON...
    dict2json(
        backup_authorities,
        os.path.join(
            batch_modifications_dir,"backup", "backup_authorities_cleanup_main_heading-" + get_current_date() + ".json"
        ),
    )
    dict2json(
        changed_authorities,
        os.path.join(
            batch_modifications_dir,"changed", "cleanup_main_heading-" + get_current_date() + ".json"
        ),
    )

    print(f"Backup and changed records JSON saved. Have a look at them before pushing the changes via API.")

    input()

    put_changes_authorities_via_koha_api(changed_authorities)



# NOT WORKING
def import_thumbs():
    ### TESTING ###

    biblio_item = 1637

    image_path = os.path.join("tmp","thumbs","20134135_009.jpg")

    upload_image_to_record(image_path,biblio_item,my_session,upload_url)


### CODE ###

### IMPORT Authority and Catalogue dictionaries

auth_dict = import_auth_dict()

#cat_dict = import_cat_dict()


### Apply changes

#cleanup_main_headings(auth_dict)

#external_sources_labels(auth_dict)

#wikidata_enhancing(auth_dict,in_progress=False)

## Put last authorities changes

#changed_authorities = json2dict(os.path.join(batch_modifications_dir,"changed","changed_authorities_wikidata-2026-03-22.json"))

#put_changes_authorities_via_koha_api(changed_authorities)





