import sys

sys.path.append("./modules")

from modules.utilities import *
from modules.relations_spotting import *

import requests
#from requests_oauth2client import OAuth2Client, OAuth2ClientCredentialsAuth

#from pagexml.parser import parse_pagexml_file

#from xml import etree

import xml.etree.ElementTree as ET
import urllib.request


# Import credentials, assuming you are running the code from the `koha` directory
credentials = json2dict("../credentials/credentials.json")

client_id = credentials["transkribus"]["user"]

client_secret = credentials["transkribus"]["password"]

auth_url = credentials["transkribus"]["auth_url"]



# Authentication using requests
transkribus_session = requests.Session()
transkribus_session.post(
	"https://transkribus.eu/TrpServer/rest/auth/login",
	data={"user": client_id, "pw": client_secret},
)


def transkribus_login():
	r = requests.post(
		"https://transkribus.eu/TrpServer/rest/auth/login",
		data={"user": client_id, "pw": client_secret},
	)
	if r.status_code == requests.codes.ok:
		return r.text
	else:
		print(r)
		print("Login failed.")
		return None


def get_transkribus_collections():
	headers = {"Accept": "application/json"}
	response = transkribus_session.get(
		"https://transkribus.eu/TrpServer/rest/collections", headers=headers
	)
	# print("REQUEST URL:", response.request.url)
	# print("REQUEST HEADERS:", response.request.headers)
	# print("REQUEST BODY (bytes):", response.request.body)
	#print("STATUS:", response.status_code)
	# print("RESPONSE HEADERS:", response.headers)
	# print("RESPONSE TEXT (truncated):", (response.text or "")[:1000])
	# input()
	return response.json()


def get_transkribus_documents(collection_id): # Returns a dictionary of documentIds and their metadata
	headers = {"Accept": "application/json"}
	response = transkribus_session.get(
		f"https://transkribus.eu/TrpServer/rest/collections/{collection_id}/list",
		headers=headers,
	)
	# print("REQUEST URL:", response.request.url)
	# print("REQUEST HEADERS:", response.request.headers)
	# print("REQUEST BODY (bytes):", response.request.body)
	#print("STATUS:", response.status_code)
	# print("RESPONSE HEADERS:", response.headers)
	# print("RESPONSE TEXT (truncated):", (response.text or "")[:1000])
	# input()
	return response.json()


def get_transkribus_complete_documents(collection_id): # Returns a full dictionary of documents, including pages metadata
	headers = {"Accept": "application/json"}
	collection = transkribus_session.get(
		f"https://transkribus.eu/TrpServer/rest/collections/{collection_id}/list",
		headers=headers,
	).json()

	documents = []

	for document in collection:
		document = transkribus_session.get(
			f"https://transkribus.eu/TrpServer/rest/collections/{collection_id}/{document["docId"]}/fulldoc",
			headers=headers,
		)

		# print("REQUEST URL:", response.request.url)
		# print("REQUEST HEADERS:", response.request.headers)
		# print("REQUEST BODY (bytes):", response.request.body)
		#print("STATUS:", document.status_code)
		# print("RESPONSE HEADERS:", response.headers)
		#print("RESPONSE TEXT :", (document.text or ""))

		documents.append(document.json())

	return documents

def get_transkribus_pages_list(collection_id,document_id,allow_filter=True,criterium="GT"): # Returns dictionary of pages with filename, XML url and PageId 
	headers = {"Accept": "application/json"}
	document = transkribus_session.get(
			f"https://transkribus.eu/TrpServer/rest/collections/{collection_id}/{document_id}/fulldoc",
			headers=headers,
		).json()

	pages_metadata = []

	for page in document["pageList"]["pages"]:
		try:
			if not allow_filter: # no specific filters
				latest_xml_version = page["tsList"]["transcripts"][0]["url"]
				pages_metadata.append({
					"pageId": page["pageId"],
					"filename": page["imgFileName"],
					"library_identifier": page["imgFileName"].split("_")[0],
					"page_number": page["imgFileName"].split("_")[1].split(".")[0],
					"image_format": page["imgFileName"].split("_")[1].split(".")[1],
					"xml_url": latest_xml_version
					})
			else: # allow filter, according to status transcript criterium
				# check if latest transcript has status = criterium
				latest_status = page["tsList"]["transcripts"][0]["status"]
				latest_xml_version = page["tsList"]["transcripts"][0]["url"]
				if latest_status == criterium:
					pages_metadata.append({
						"collection_id": collection_id,
						"document_id": document_id,
						"pageId": page["pageId"],
						"filename": page["imgFileName"],
						"library_identifier": page["imgFileName"].split("_")[0],
						"page_number": page["imgFileName"].split("_")[1].split(".")[0],
						"image_format": page["imgFileName"].split("_")[1].split(".")[1],
						"xml_url": latest_xml_version
						})
		except IndexError:
			print(f"Formatting errors for current page: {page["pageNr"]} ")

	print(f"Number of pages imported: {len(pages_metadata)}")


	return pages_metadata

def get_page_xml_transkribus_api(collection_id,document_id,page_number):
	headers = {"Accept": "application/xml"}
	page_xml = transkribus_session.get(
			f"https://transkribus.eu/TrpServer/rest/collections/{collection_id}/{document_id}/{page_number}/text",
			headers=headers,
		)
	print(page_xml.content)
	return page_xml

def post_page_xml_transkribus_api(collection_id,document_id,page_number,page_xml_filepath):
	headers = {"Content-Type": "application/xml"}
	page_xml_file = open(page_xml_filepath,'rb')
	page_xml_data = page_xml_file.read()
	page_xml_file.close()
	page_xml_response = transkribus_session.post(
			f"https://transkribus.eu/TrpServer/rest/collections/{collection_id}/{document_id}/{page_number}/text",
			headers=headers,
			data=page_xml_data
		)
	print("STATUS:", page_xml_response.status_code)
	print("RESPONSE HEADERS:", page_xml_response.headers)
	print("RESPONSE TEXT :", (page_xml_response.text or ""))
	return page_xml_response

def relations_spotting_from_page_xml(page_xml_file):
	tree = ET.parse(page_xml_file)

	# Avoid additional ns0: ns1: namespace issues after rewriting
	ET.register_namespace("", "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15")

	root = tree.getroot()

	regions = get_regions_from_xml(root,baseline=False)
	# Generate relations dictionary according to clustering method
	#relations = simple_relations_matching(regions)
	print("Which clustering algorithm would you like to use? 1 = simple, 2 = complex multicolumns:")
	answer = int(input())
	if answer == 2:
		relations = vertical_clustering_relations_matching(regions)
	else:
		relations = vertical_clustering_relations_matching_v1(regions)

	# Ingest relations dictionary back to PAGE XML
	root = ingest_relations_to_xml(relations,root)

	# Export modified PAGE XML to new file
	ET.indent(tree, space='  ', level=0)
	tree.write(page_xml_file.replace(".xml","_with_relations.xml"), encoding="utf-8", xml_declaration=True,method='xml')

def spot_relations_to_api(collection_metadata,collection_id,document_id,page_number):

	#page_xml_response = get_page_xml_transkribus_api(collection_id,document_id,page_number)

	# Get page_xml filename from metadata 
	for document in collection_metadata["documents"]:
		if document["md"]['docId'] == document_id:
			document_metadata = document
			break

	page_metadata = list(filter(lambda x: x["pageNr"] == page_number, document_metadata["pageList"]["pages"]))[0]

	page_filename = page_metadata["imgFileName"].replace(".jpg",".xml")

	page_xml_filepath = os.path.join("tmp",page_filename)
	page_xml_url = page_metadata["tsList"]["transcripts"][0]["url"]	

	if len(page_metadata) > 0:
		urllib.request.urlretrieve(page_xml_url, page_xml_filepath)
		print(f"Downloading {page_xml_url} to {page_xml_filepath}...")


	# Process relations from page_xml -> a temp file is create

	relations_spotting_from_page_xml(page_xml_filepath)

	print("Saving relations via Transkribus API")
	post_page_xml_transkribus_api(collection_id,document_id,page_number,page_xml_filepath.replace(".xml","_with_relations.xml"))

	
def get_page_xml(pages_metadata,page_xml_directory,json_directory): # this script get the PAGE XML file of a page and converts it into JSON

	for page in pages_metadata:
		# get the XML file from Transkribus
		headers = {"Accept": "application/xml"}
		page_xml_response = transkribus_session.get(page["xml_url"],headers=headers)
		#print("STATUS:", page_xml_response.status_code)
		#print("RESPONSE HEADERS:", page_xml_response.headers)
		#print("RESPONSE TEXT :", (page_xml_response.text or ""))

		# save response to xml file
		if not os.path.exists(os.path.join(page_xml_directory,page["library_identifier"])):
			os.makedirs(os.path.join(page_xml_directory,page["library_identifier"]))

		page_filename = os.path.join(page_xml_directory,page["library_identifier"],f"{page["filename"].split(".")[0]}.xml")

		page_file = open(page_filename,'w')

		page_file.write(page_xml_response.text)

		page_file.close()

		# parse xml using pagexml-tools library, unfortunately without relations

		#page_doc = parse_pagexml_file(page_filename)

		# getting information manually via xml

		regions = []

		relations = []

		page_file = open(page_filename,'r')

		page_byte = page_file.read().encode('utf-8')

		tree = ET.parse(page_filename)

		root = tree.getroot()

		# get relations

		xml_relations = root.findall("./{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}Page/{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}Relations/{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}Relation")
		# I am assuming multiple links
		for child in xml_relations:
			try:
				relations.append({"type": child.attrib["custom"].split("value:")[1].split(";")[0]})
				xml_regions = child.findall("./{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}RegionRef")
				try:
					for xml_region in enumerate(xml_regions): 
						if xml_region[0] == 0: # get source
							relations[-1]["source"] = xml_region[1].attrib["regionRef"]
						else:
							relations[-1]["target"] = xml_region[1].attrib["regionRef"]
				except Exception:
					print(f"Malformatted relation {page_filename}")
					print(f"xml_relations: {xml_relations.text}")
					print(f"xml_regions: {xml_regions.text}")
					input()
			except AttributeError:
				pass


		# get text_regions with type,id and text value

		xml_regions = root.findall("./{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}Page/{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}TextRegion")
		
		for xml_region in xml_regions:
			try:
				region_type = xml_region.attrib["custom"].split("type:")[1].split(";")[0]
			except IndexError:
				region_type = ""
			regions.append({
					"region_id": xml_region.attrib["id"],
					"type": region_type,
					"text": []
					}
					)
			xml_textlines = xml_region.findall("./{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}TextLine")
			for  xml_line in xml_textlines:
				regions[-1]["text"].append(xml_line.find("./{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}TextEquiv/{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}Unicode").text)


		# export values to custom JSON serialization

		if not os.path.exists(os.path.join(json_directory,page["library_identifier"])):
			os.makedirs(os.path.join(json_directory,page["library_identifier"]))

		page_filename = os.path.join(json_directory,page["library_identifier"],f"{page["filename"].split(".")[0]}.json")

		dict2json({
			"collection_id": page["collection_id"], 
			"document_id": page["document_id"], 
			"page_id": page["pageId"], 
			"library_identifier": page["library_identifier"], 
			"page_number": page["page_number"], 
			"regions": regions, 
			"relations": relations},
			page_filename)



def get_jpg_image_from_transkribus(page_metadata,output_directory="./tmp"): # Saves the JPG image from Transkribus to tmp and returns the filepath
	image_url = page_metadata["url"]
	# Save the JPG image using urllib
	urllib.request.urlretrieve(image_url,os.path.join(output_directory,page_metadata["imgFileName"]))

	return os.path.join(output_directory,page_metadata["imgFileName"])
					









		
			


		


	




