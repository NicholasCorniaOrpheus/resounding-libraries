"""Main script for Transkribus import to Koha """

import sys

sys.path.append("./modules")

from modules.utilities import *
from modules.transkribus import *
from modules.relations_spotting import *
from modules.authority_recognition import *
from modules.digital_images import *
from modules.koha import *

page_xml_data_directory = os.path.join("data", "page_xml")

json_data_directory = os.path.join("data", "json")

indices_tk_training_id = 257292

credentials = json2dict("../credentials/credentials.json")

oauth_credentials = credentials["koha"]["oauth_credentials"]

client_id = oauth_credentials["client_id"]

client_secret = oauth_credentials["secret_key"]

user_agent = oauth_credentials["user_agent"]

base_url = credentials["koha"]["koha_api_url"]

transkribus_user = credentials["transkribus"]["user"]

transkribus_password = credentials["transkribus"]["password"]

koha_session = oauth2_session(client_id, client_secret, user_agent, base_url)

transkribus_session = transkribus_api_login(transkribus_user,transkribus_password)

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

def save_transkribus_collections_metadata(metadata_directory:str, session):
	collections_api = get_transkribus_collections(session)
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

def import_collection_metadata(collection_id=257292,session=transkribus_session):
	print("Would you like to update the local metadata? y/n")
	answer = input()
	if answer == "y":
		print("Importing latest collections metadata from Transkribus API...")
		save_transkribus_collections_metadata("./metadata",session)

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

def match_keywords_from_barcode(koha_session=koha_session,transkribus_session=transkribus_session,output_directory="./data/authority_matching",collection_id=257292,zfill=3,pages=True):
	"""
	1. User provides barcode of index manually | document_id + page_number
	2. Get keywords from index via barcode
	3. Retrieve PAGEXML file from Transkribus API
	4. Fuzz matching transcription with keywords list
	5. Update XML and push it back to  Transkribus via API
	"""
	# Import collection metadata
	print(f"Ton Koopman Indices collection id: {collection_id}")
	collection_metadata = import_collection_metadata(collection_id=collection_id,session=transkribus_session)

	# User provides document ID and page number
	print("Insert document id to be processed: ")
	document_id = int(input())
	print("Choose page:")
	page_number = int(input())
	# Get page_metadata
	document_pages = get_transkribus_pages_list(collection_id,document_id,allow_filter=False)

	page_metadata = list(filter(lambda x: x["pageNr"] == page_number,document_pages))[0]
	#print(page_metadata)


	# Get keywords from index via barcode
	barcode = page_metadata["library_identifier"]

	# create a list for the fuzz matching
	keywords = extract_keywords_from_barcode(session=koha_session,base_url=base_url,barcode=barcode,mapping=biblionumber_mapping)
	

	#Get automatic transcripts from Transkribus API
	xml_url = page_metadata["xml_url"]
	layout = get_regions_and_relations_from_xml(xml_url=xml_url,session=transkribus_session)

	# Parse PAGEXML 
	headers = {"Accept": "application/xml"}
	page_xml_response = transkribus_session.get(page_metadata["xml_url"],headers=headers)
	xml_string = page_xml_response.text
	root = ET.fromstring(xml_string.encode('utf-8'))

	for region in layout["regions"]:
		# combine text list into unique string
		if region["type"] in ["keyword","keyword_auth"]:
			# consider only one baseline region
			if len(region["text"]) <= 1:
				text = region["text"][0]
				scores = match_with_threshold(text.replace(":",""),keywords)
				# get the best result and substitute it to the text region
				if len(scores) > 0:
					region["keyword"] = {"m_heading": scores[0]["m_heading"],"auth_id": scores[0]["auth_id"], "score": scores[0]["average_score"] }
					if ":" in text:
						# combine keyword value and :
						region["text"][0] = f"{scores[0]["m_heading"]} :"
					else:
						region["text"][0] = scores[0]["m_heading"]

					# pull back the new keyword to the PAGEXML file
					# get region by id
					xml_region = root.findall(f'''.//*[@id="{region["region_id"]}"]''')[0]
					# change structural tag type to keyword_auth
					xml_region.set("custom",xml_region.get("custom").replace("keyword;","keyword_auth;"))
					# get text
					xml_textline = xml_region.findall(".//{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}TextLine")[0]
					xml_unicode = xml_textline.find("./{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}TextEquiv/{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}Unicode")
					# update text value
					xml_unicode.text = region["text"][0]
					#print(f"Updated region {region['region_id']} with keyword {region['keyword']['m_heading']} with score {region['keyword']['score']}")

		### TO BE CHECKED!!!!!
		elif region["type"] in ["pages-keyword","pages-keyword_auth"]:
				# consider only one baseline region
				if len(region["text"]) <= 1:
					text = region["text"][0]
					scores = match_with_threshold(text.replace(":",""),keywords,list_field="pages")
					# get the best result and substitute it to the text region
					if len(scores) > 0:
						region["keyword"] = {"pages": scores[0]["pages"],"auth_id": scores[0]["auth_id"], "score": scores[0]["average_score"] }
						if ":" in text:
							# combine keyword value and :
							region["text"][0] = f"{scores[0]["pages"]} :"
						else:
							region["text"][0] = scores[0]["pages"]

						# pull back the new keyword to the PAGEXML file
						# get region by id
						xml_region = root.findall(f'''.//*[@id="{region["region_id"]}"]''')[0]
						# change structural tag type to keyword_auth
						xml_region.set("custom",xml_region.get("custom").replace("pages-keyword;","pages-keyword_auth;"))
						# get text
						xml_textline = xml_region.findall(".//{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}TextLine")[0]
						xml_unicode = xml_textline.find("./{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}TextEquiv/{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}Unicode")
						# update text value
						xml_unicode.text = region["text"][0]
						#print(f"Updated region {region['region_id']} with keyword {region['keyword']['m_heading']} with score {region['keyword']['score']}")

	# update PAGEXML back to Transkribus API
	new_xml = ET.tostring(root, encoding="utf-8")

	page_xml_response = transkribus_session.post(
			f"https://transkribus.eu/TrpServer/rest/collections/{collection_id}/{document_id}/{page_number}/text",
			headers=headers,
			data=new_xml
		)

	print(page_xml_response.status_code)


	# export result to JSON
	print(f"Exporting JSON to {os.path.join(output_directory,page_metadata["filename"].replace(".jpg",".json"))}")
	dict2json(layout,os.path.join(output_directory,page_metadata["filename"].replace(".jpg",".json")))

	

def save_filtered_authorities():

	auth_dict_file = get_latest_file(os.path.join("data","auth_dict"))
	print(f"Importing latest Koha Authorities dictionary: {auth_dict_file} ...")
	auth_dict = json2dict(auth_dict_file)

	print("Filtering authorities for word-matching algorithm...")
	filtered_auth = import_koha_authorities(auth_dict)

	output_file = os.path.join("data","filtered_auth","filtered_auth-"+get_current_date()+".json")
	print(f"Save filtered authorities to {output_file} ...")
	dict2json(filtered_auth,output_file)

### CODE


#match_keyword_with_authority()

#match_keywords_from_barcode()

	
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