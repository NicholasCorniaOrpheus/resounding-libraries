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

# Mappings

marc2json_mapping = os.path.join("data", "mappings", "mapping_marc_fields.json")
abbreviation_mapping = os.path.join(
    "data", "mappings", "mapping_abbreviation_codes.json"
)
external_sources_mapping = os.path.join(
    "data", "mappings", "mapping_external_sources.json"
)

reports_mapping = os.path.join("data", "mappings", "mapping_reports.json")


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


def clean_field_336():
    # clean Field 336 from records
    print("Clean Field 336 from records")
    clean_field_from_records("336", get_latest_file(biblioitems_marc_dir))


### CODE ###

cat_dict = generate_catalogue_dict(get_latest_file(biblioitems_marc_dir))

cat_dict, items_to_be_processed = clean_field_from_catalogue_dict(cat_dict, "336")

print(f"Number of items to be processed: {len(items_to_be_processed)}")

print(f"First 10 values: {items_to_be_processed[0:9]} ")


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
