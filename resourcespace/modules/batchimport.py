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
def folders2collections(basepath):
    collection_list = []
    sorted_directory = sorted(os.scandir(basepath), key=lambda e: e.name)
    for d in sorted_directory:
        collection_list.append(d.name)

    return collection_list


def add_collection2parent_biblioitem(
    collection_name, collection_metadata, rs_collection_tree_list
):
    # to-do: according to biblioitem metadata
    pass


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
        print(rs_metadata)


def create_biblioitems_collections(collection_metadata_list):
    # filters all needed biblioitems and create new parent collections for the new digitizations
    pass


# returns a list of IDs given a list of collection names
def create_collections(collection_list):
    new_collections_ids = []
    for element in collection_list:
        res = apiQuery(
            credentials=credentials,
            query=rsQueries["create_collection"],
            parameters=[element],
        )

        new_collections_ids.append(res.json())

    return new_collections_ids


def add_multiple_resources2collection(
    list_resources, collection_id
):  # add a list of resources IDs to a collection ID
    for resource_id in list_resources:
        apiQuery(
            credentials=credentials,
            query=rsQueries["add_resource_to_collection"],
            parameters=[str(resource_id), str(collection_id)],
        )
