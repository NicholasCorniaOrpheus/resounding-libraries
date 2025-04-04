"""
Utility fuctions for batch operations
"""

import json
import os
import requests

import sys

sys.path.append("./modules")

from modules.api import *
from modules.utilities import *
from modules.koha_metadata import *


# returns an ordered list of collection names based on folders
def folders2collection_list(basepath):
    collection_list = []
    sorted_directory = sorted(os.scandir(basepath), key=lambda e: e.name)
    for d in sorted_directory:
        collection_list.append(d.name)

    return collection_list


# I assume the collection name = Koha barcode
def get_collection_metadata_from_koha(
    collection_list, koha_catalogue_dict, mapping_rs_fields_dict, digitization_quality
):
    collection_metadata_list = []
    for item in collection_list:
        biblioitem = retrieve_biblioitem_from_barcode(item, koha_catalogue_dict)
        rs_metadata = biblioitem2rs_metadata(
            biblioitem,
            item,
            mapping_rs_fields_dict,
            digitization_quality,
        )
        collection_metadata_list.append(rs_metadata)

    return collection_metadata_list


def check_duplicates(collection_name, rs_collection_tree):
    query = list(
        filter(lambda x: x["collection_name"] == collection_name, rs_collection_tree)
    )
    if len(query) > 0:
        print("Found duplicated: \n", query[0])
        return True
    else:
        return False


def create_collections_and_resourcers_from_metadata_list(
    collection_metadata_list,rs_collection_tree, credentials, ingestion_path, resource_type
):
    # filters all needed biblioitems and create new parent collections for the new digitizations
    for item in collection_metadata_list:
        if check_duplicates(item["barcode"],rs_collection_tree):
            print("Barcode resource already present in RS: skip import.")
            pass
            
        else:
            # check if biblionumber collection is already present
            if check_duplicates(item["biblionumberid"],rs_collection_tree):
                # append barcode_collection to existing biblionumber collection
                query = list(filer(lambda x: x["collection_name"] == item["biblionumberid"], rs_collection_tree))
                biblionumber_collection_id = query[0]["id"]
                print(f"Biblionumber {item["biblionumberid"]} already present as collection id {biblionumber_collection_id}")
                input()
            else:
                # create a new collection with given biblionumber
                biblionumber_collection_id = int(rs_API_cURL_POST(credentials, "create_collection", parameters=[item["biblionumberid"]]))
                print(f"New collection created for biblionumber {item["biblionumberid"]}: {biblionumber_collection_id}")
                # append new collection to root
                add_parent2collection(biblionumber_collection_id, rs_collection_tree[0]["id"], credentials)
                input()
                
            # create a new collection with given barcode
            barcode_collection_id = int(rs_API_cURL_POST(credentials, "create_collection", parameters=[item["barcode"]]))
            print(f"New collection created for barcode {item["barcode"]}: {barcode_collection_id}")
            # biblionumber is parent of barcode
            add_parent2collection(barcode_collection_id, biblionumber_collection_id, credentials)
            # add biblionumber and barcode to rs_collection_tree
            rs_collection_tree.append(
                    {
                            "collection_name": item["biblionumberid"],
                            "id": biblionumber_collection_id,
                            "parent": rs_collection_tree[0]["id"],
                            "children_ids": [barcode_collection_id],
                            "resources_ids": [],
                        }
                )
            rs_collection_tree.append(
                    {
                            "collection_name": item["barcode"],
                            "id": barcode_collection_id,
                            "parent": biblionumber_collection_id,
                            "children_ids": [],
                            "resources_ids": [],
                        }
                )
            input()
            # create resources from path + metadata
            sorted_directory = sorted(os.scandir(os.path.join(ingestion_path,item["barcode"])), key=lambda e: e.name)
            i = 0
            for file in sorted_directory:
                # create new resource
                i += 1
                resource_id = int(rs_API_cURL_POST(credentials, "create_resource", parameters=[str(resource_type)]))
                print(f"New resource created for file {file.name}: {resource_id}")
                rs_collection_tree[-1]["resources_ids"].append(resource_id)
                # upload file to resource
                print("Uploading resource to RS...")
                rs_API_cURL_POST(credentials,query_name="upload_file",parameters=[str(resource_id), "0", "0", "0", os.path.join(ingestion_path,item["barcode"],file.name) ])
                # add relevant metadata
                print("Adding metadata and IIIF identifiers...")
                for field in item.keys():
                    if field == "iiifidentifier":
                        # setting IIIF identifier = collection_id
                        rs_API_cURL_POST(credentials,query_name="update_field",parameters=[str(resource_id),field,str(barcode_collection_id)])
                    if field == "iiifsequencefield":
                        # incrementing sequence field
                        rs_API_cURL_POST(credentials,query_name="update_field",parameters=[str(resource_id),field,str(i)])
                    if field not in ["iiifidentifier","iiifsequencefield"]:
                        if len(item[field]) >1:
                            value = ""
                            for entry in item[field]:
                                value += revert_personal_names_with_comma(entry) +","
                            value = value[:-1]

                        else:
                            value = revert_personal_names_with_comma(item[field][0])
                        
                        rs_API_cURL_POST(credentials,query_name="update_field",parameters=[str(resource_id),field,value])    


            


# returns a list of IDs given a list of collection names
def create_collections(collection_list, credentials):
    # to be finished

    return new_collections_ids


def add_multiple_resources2collection(
    list_resources, collection_id, credentials
):  # add a list of resources IDs to a collection ID
    # to be finished

    return True
