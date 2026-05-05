"""Main script for Transkribus import to Koha """

import sys

sys.path.append("./modules")

from modules.utilities import *
from modules.transkribus import *
from modules.relations_spotting import *
from modules.authority_recognition import *
from modules.digital_images import *


page_xml_data_directory = os.path.join("data", "page_xml")

json_data_directory = os.path.join("data", "json")

indices_tk_training_id = 257292

credentials = json2dict("../credentials/credentials.json")

oauth_credentials = credentials["koha"]["oauth_credentials"]

client_id = oauth_credentials["client_id"]

client_secret = oauth_credentials["secret_key"]

user_agent = oauth_credentials["user_agent"]

base_url = credentials["koha"]["koha_api_url"]

session = oauth2_session(client_id, client_secret, user_agent, base_url)

biblionumber_mapping_filepath = os.path.join("data","mappings","call_number-barcode.csv")

biblionumber_mapping = import_biblionumber_shelfmark_barcode_mapping(biblionumber_mapping_filepath)

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

def convert_pdfs_to_images_bulk():
	directories_path = os.path.join(
	"data", "digital_images", "special_collections-shelfmark"
	)
	print(f"Digital images parent directory: {directories_path}")

	output_path = os.path.join("data", "digital_images", "special_collections-barcode")

	print(f"Digital images output parent directory: {output_path}")

	convert_pdfs_to_images(directories_path, output_path,os.path.join("data","mappings","call_number-barcode.csv"))

	


### TEST ####

def match_keywords_fron_barcode(collection_id=257292,zfill=3):
	"""
	1. User provides barcode of index manually | document_id + page_number
	2. Get keywords from index via barcode
	3. Retrieve PAGEXML file from Transkribus API
	4. Fuzz matching transcription with keywords list
	5. Update XML and push it back to  Transkribus via API
	"""
	# Import collection metadata
	print(f"Ton Koopman Indices collection id: {collection_id}")
	collection_metadata = import_collection_metadata(collection_id=collection_id)

	# User provides document ID and page number
	print("Insert document id to be processed: ")
	document_id = int(input())
	print("Choose page:")
	page_number = int(input())
	# Get page_metadata
	document_pages = get_transkribus_pages_list(collection_id,document_id,allow_filter=False)

	page_metadata = list(filter(lambda x: x["pageNr"] == page_number,document_pages))[0]


	# Get keywords from index via barcode
	barcode = page_metadata["library_identifier"]

	keywords = extract_keywords_from_barcode(barcode=barcode,mapping=biblionumber_mapping)

	# TO BE CONTINUED...
	# create a list for the fuzz matching


	#Get automatic transcripts from Transkribus API
	xml_url = page_metadata["xml_url"]

	layout = get_regions_and_relations_from_xml(xml_url,session)

	"""
	- for each region extract text
	- match text against keywords list and return best match, or None based on heuristic threshold.
	- if not None overwrite string back to XML region (using region_id)
	- DON'T forget to add ":" back to keyword if needed.







	




	




	#get_page_xml_transkribus_api()


def extract_keywords_from_barcode(barcode: str, mapping: list) -> list:
	"""
	Given a barcode, extracts a list of keywords.

	Args:
	barcode (str): Barcode string.
	mapping (list): Biblionumber-shelfmark-barcode mapping from CSV.
	Returns:
	keywords (list): List of dictionaries for keywords.

	Examples:
	>>>

	"""
	# get biblionumber from barcode
	biblionumber = None 
	for item in mapping:
		if item["barcode"] == barcode:
			biblionumber = item["biblionumber"]
			break
	if biblionumber is not None:

		biblio = get_biblionumber_marc(session,base_url,biblionumber)

		keywords = get_koopman_keywords(biblio,barcode)

	else:
		print(f"Barcode {barcode} not found! Skip...")


	return keywords


def match_keyword_with_authority():

	auth_dict_file = get_latest_file(os.path.join("data","auth_dict"))
	print(f"Importing latest Koha Authorities dictionary: {auth_dict_file} ...")
	auth_dict = json2dict(auth_dict_file)

	print("Filtering authorities for word-matching algorithm...")
	filtered_auth = import_koha_authorities(auth_dict)

	word = "viool"
	match_with_threshold(word,filtered_auth)

	output_file = os.path.join("data","filtered_auth","filtered_auth-"+get_current_date()+".json")
	print(f"Save filtered authorities to {output_file} ...")
	dict2json(filtered_auth,output_file)

### CODE

#extract_keywords_from_barcode(barcode="20122119",mapping=biblionumber_mapping)

#match_keyword_with_authority()

match_keywords_fron_barcode()

input()
	
collection_id = 257292


print(f"Ton Koopman Indices collection id: {collection_id}")
collection_metadata = import_collection_metadata(collection_id=collection_id)


print("Insert document id to be processed: ")
document_id = int(input())

keep_editing = True 

while keep_editing is True:
	print("Choose page:")

	page_number = int(input())

	spot_relations_to_api(collection_metadata,collection_id,document_id,page_number)

	print("Would you like to process another page? y/n")
	answer = input()
	if answer == "y":
		keep_editing = True
	else:
		keep_editing = False

#import_transkribus_tk_indices()