import sys

sys.path.append("./modules")

from modules.utilities import *

import requests
#from requests_oauth2client import OAuth2Client, OAuth2ClientCredentialsAuth

from pagexml.parser import parse_pagexml_file

#from lxml import etree

import xml.etree.ElementTree as ET

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
	print("STATUS:", response.status_code)
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
	print("STATUS:", response.status_code)
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
		print("STATUS:", document.status_code)
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

	print(f"Number of pages imported: {len(pages_metadata)}")


	return pages_metadata

	
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
				for i in range(2): 
					if i == 0: # get source
						relations[-1]["source"] = xml_regions[i].attrib["regionRef"]
					else:
						relations[-1]["target"] = xml_regions[i].attrib["regionRef"]
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









		
			


		


	
