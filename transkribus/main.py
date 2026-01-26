"""Main script for Transkribus import to Koha """

import sys

sys.path.append("./modules")

from modules.utilities import *
from modules.transkribus import *
from modules.relations_spotting import *



page_xml_data_directory = os.path.join("data", "page_xml")

json_data_directory = os.path.join("data", "json")

indices_tk_training_id = 257292

# get_transkribus_collections()

# TEST succesfull and ready for production

#pages_metadata = get_transkribus_pages_list(collection_id=257292, document_id=1702668)

#get_page_xml(pages_metadata, page_xml_data_directory, json_data_directory)

#### TO-DO:

"""

- Export json data to unique csv {library_identifier,keyword,pages} according to relations and separator for multiple lines
- Map keywords to existing authorities in Koha (get Ton Koopman Keywords from report)
- Record keywords and related pages via the 653 field in Koha via API (retrieve barcode or identifier-> get biblio_id and items)

- Debugging document 4086215 : malformatted relations! Missing regionRef value.
- Problem of naming cell3 selection. They are not conformed with the naming convention... Traskribus Expert Client is the only way to change metadata after import.

"""

### FUNCTIONS


def import_transkribus_tk_indices(
	indices_tk_training=257292, allow_filter=True, criterium="GT"
):  # Pulls transcriptions and PAGE XML from Ton Koopman collection. The default assumption is that only Ground Truth pages will be processed.
	# get the collection from Transkribus API
	collection = get_transkribus_documents(indices_tk_training_id)

	# for each document in collection, generate page_xml and JSON data
	n_doc = len(collection)
	i = 0
	for document in collection:
		print(f"Processing document {document["docId"]}...")
		i +=1
		pages_metadata = get_transkribus_pages_list(
			collection_id=indices_tk_training, document_id=document["docId"],allow_filter=allow_filter,
				criterium=criterium,
		)

		# store PAGE XML and JSON data for each page according to library identifier (barcode, or old shelfmark)
		for page in pages_metadata:
			get_page_xml(
				pages_metadata,
				page_xml_data_directory,
				json_data_directory
			)

		print(f"{float(i)/n_doc*100}%")

def save_transkribus_collections_metadata(metadata_directory):
	collections_api = get_transkribus_collections()
	collection_list = []
	for collection in collections_api["trpCollection"]:
		collection_list.append({"collection_id": collection["colId"],
			"collection_name": collection["colName"]})
	#print(collection_list)
	#input()

	for collection in collection_list:
		collection_id = collection["collection_id"]
		collection_documents = get_transkribus_complete_documents(collection_id)
		collection_name = collection["collection_name"].replace(" ","_")
		transkribus_metadata = {
			"collection_id": collection_id,
			"collection_name": collection_name,
			"documents": collection_documents
			}

		# Export to JSON
		dict2json(transkribus_metadata,os.path.join(metadata_directory,f"{collection_id}.json"))



def transkribus_indices_to_csv():
	pass

def transkribus_indices_to_koha():
	pass

def import_collection_metadata(collection_id=257292):
	print("Would you like to update the local metadata? y/n")
	answer = input()
	if answer == "y":
		print("Importing latest collections metadata from Transkribus API...")
		save_transkribus_collections_metadata("./metadata")

	return json2dict(os.path.join("metadata",f"{collection_id}.json"))





### TEST ####

#transkribus_pages_directory = os.path.join("data", "page_xml")

#transkribus_pages_directory = os.path.join("tmp")

#test_page_xml = os.path.join(transkribus_pages_directory, "12D02-1", "12D02-1_002.xml")

#test_page_xml = os.path.join(transkribus_pages_directory,"20124686_002.xml")






#get_page_xml_transkribus_api(collection_id,document_id,page_number)

#relations_spotting_from_page_xml(test_page_xml)

#get_page_xml_transkribus_api(collection_id,document_id,page_number)
#input()

#post_page_xml_transkribus_api(collection_id,document_id,page_number,test_page_xml.replace(".xml","_with_relations.xml"))

#post_page_xml_transkribus_api(collection_id,document_id,page_number,test_page_xml)




# TO BE CONTINUED

"""
- Save coordinates and centroids in JSON serialization file
- Get from Transkribus API pages that are not Ground Truth, but have regional labels (In Progress)
- Match keyword with pages-keywords regions accoring to their centroids x coordinate, according to minimal distance criterium.
- Parse relations back to PAGE XML
- PUT modified PAGE XML back to Transkribus

"""


### CODE

collection_id = 257292

#document_id = 1860507 # facsimiles-scans 2024-

document_id = 8184307 # bach

page_number = 2

print(f"Ton Koopman Indices collection id: {collection_id}")
collection_metadata = import_collection_metadata(collection_id=collection_id)

#get_jpg_image(collection_metadata,document_id,page_number)

#spot_relations_to_api(collection_metadata,collection_id,document_id,page_number)

#import_transkribus_tk_indices()