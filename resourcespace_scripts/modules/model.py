'''
Utility fuctions for batch operations
'''

import json
import os
import requests

import sys
sys.path.append("./modules")

from modules.api import *
from modules.koha_api import *

# KOHA API
# ingest metadata


# returns an ordered list of collection names based on folders
def Folders2Collections(basepath):
	collection_list = []
	sorted_directory = sorted(os.scandir(basepath), key=lambda e: e.name)
	for d in sorted_directory:
		collection_list.append(d.name)

	return collection_list


# returns a list of IDs given a list of collection names
def createCollections(collection_list):
	new_collections_ids = []
	for element in collection_list:
	    res = apiQuery(
	        credentials=credentials,
	        query=rsQueries["create_collection"],
	        parameters=[element],
	    )
    
    	new_collections_ids.append(res.json())

    return new_collections_ids 

def addMultipleResourcesToCollection(list_resources, collection_id): # add a list of resources IDs to a collection ID
    for resource_id in list_resources:
        apiQuery(
            credentials=credentials,
            query=rsQueries["add_resource_to_collection"],
            parameters=[str(resource_id), str(collection_id)],
        )


