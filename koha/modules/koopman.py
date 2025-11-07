"""
Scripts for Special Collection of Ton Kooman
"""

import sys

sys.path.append("./modules")  # importing custom functions in modules
from modules.utilities import *


def special_collection2csv(
    biblioitems_dir,
    export_dir,
    source_of_acquisition="Koopman",
    exclude_section="KTS1 C",
):
    # load latest biblioitems to dictionary
    biblioitems = json2dict(get_latest_file(biblioitems_dir))

    special_collection = []

    incomplete_records = []

    source_code = "Koopman"
    for biblio in biblioitems:
        for item in biblio["items"]:
            if only_modern_collection:  # select only books outside the cells
                try:
                    if (
                        item["source_of_acquisition"] == source_of_acquisition
                        and exclude_section not in item["call_number"]
                    ):
                        special_collection.append(
                            {
                                "biblioitem": biblio["biblioitem"][0]["id"],
                                "title": biblio["title"][0]["string"],
                                "call_number": item["call_number"],
                                "barcode": item["barcode"],
                                "source_of_acquisition": item["source_of_acquisition"],
                            }
                        )
                except Exception:
                    incomplete_records.append(
                        {"biblioitem": biblio["biblioitem"][0]["id"], "item": item}
                    )

            else:
                try:
                    if item["source_of_acquisition"] == source_of_acquisition:
                        special_collection.append(
                            {
                                "biblioitem": biblio["biblioitem"][0]["id"],
                                "title": biblio["title"][0]["string"],
                                "call_number": item["call_number"],
                                "barcode": item["barcode"],
                                "source_of_acquisition": item["source_of_acquisition"],
                            }
                        )
                except Exception:
                    incomplete_records.append(
                        {"biblioitem": biblio["biblioitem"][0]["id"], "item": item}
                    )

    print(f"Special collection has {len(special_collection)} items ")

    print(f"Incomplete records: {len(incomplete_records)} items ")

    print("Exporting special collection as CSV...")

    dict2csv(
        special_collection,
        os.path.join(
            export_dir,
            source_of_acquisition
            + "-special_collection-"
            + get_current_date()
            + ".csv",
        ),
    )

    dict2json(
        incomplete_records,
        os.path.join(
            export_dir,
            "incomplete_records-" + get_current_date() + ".json",
        ),
    )
