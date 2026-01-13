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
	print(collection_list)
	input()

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
		dict2json(transkribus_metadata,os.path.join(metadata_directory,f"{collection_name}-{collection_id}.json"))


def relations_spotting_from_page_xml(page_xml_file,source_region_type="keyword",target_region_type="pages-keyword",relations_type="related_pages"):
	tree = ET.parse(page_xml_file)

	# Avoid additional ns0: ns1: namespace issues after rewriting
	ET.register_namespace("", "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15")

	root = tree.getroot()

	regions = []

	# Get data from each region, including centroids and coordinates
	for text_region in root.findall("./{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}Page/{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}TextRegion"):
		coordinates = get_region_coordinates(text_region)
		try:
			region_type = text_region.attrib["custom"].split("type:")[1].split(";")[0]
		except IndexError: # in case no type is defined.
			region_type = ""
		regions.append({
			"region_id": text_region.attrib["id"],
			"type": region_type,
			"text": [],
			"coordinates": coordinates,
			"centroids": get_polygonal_centroids(coordinates)
			})
		# Get text lines
		xml_textlines = text_region.findall("./{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}TextLine")
		for  xml_line in xml_textlines:
			regions[-1]["text"].append(xml_line.find("./{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}TextEquiv/{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}Unicode").text)

	# Split regions in two ordered list (one for source and one for target) according to centroids y coordinate.
	source_regions = sorted([region for region in regions if region["type"]==source_region_type], key=lambda k: k["centroids"][1])
	target_regions = sorted([region for region in regions if region["type"]==target_region_type], key=lambda k: k["centroids"][1])

	#print(f"Source regions: {", ".join([region["region_id"] for region in source_regions])}")
	#print(f"Target regions: {", ".join([region["region_id"] for region in target_regions])}")

	# Generate relations to minimal distance criterium between source and target
	relations = []
	for source_region in source_regions:
		# get closest target region
		min_region = None
		for target_region in target_regions:
			if min_region is None:
				min_region = target_region
			else:
				if abs(source_region["centroids"][1]-target_region["centroids"][1]) < abs(source_region["centroids"][1]-min_region["centroids"][1]):
					min_region = target_region

		relations.append({
			"type": relations_type,
      		"source": source_region["region_id"],
      		"target": min_region["region_id"]
			})

	#print(f"Relations: {relations}")
	# Parse new automatic relations back to PAGE XML. This script will not overwrite existing relations

	page_xml = root.find("./{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}Page")
	
	relations_xml = root.find("./{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}Page/{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}Relations")
	if relations_xml == None: # Relations is empty
		relations_xml = ET.SubElement(page_xml,"{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}Relations")
		#page_xml.append(relations_xml)

	for relation in relations:
		# Create a new element for each relation
		relation_element = ET.Element("Relation")
		# Set attribute type to link and custom according to Transkribus notation
		relation_element.set("type","link")
		relation_element.set("custom",f"relationName {{value:{relation['type']};}}")
		# Generate subelement RegionRef for source and target
		source_region_ref = ET.Element("RegionRef")
		source_region_ref.set("regionRef",relation["source"])
		target_region_ref = ET.Element("RegionRef")
		target_region_ref.set("regionRef",relation["target"])
		relation_element.append(source_region_ref)
		relation_element.append(target_region_ref)
		relations_xml.append(relation_element)


	# Export modified PAGE XML to new file
	ET.indent(tree, space='  ', level=0)
	tree.write(test_page_xml.replace(".xml","_with_relations.xml"), encoding="utf-8", xml_declaration=True,method='xml')



def transkribus_indices_to_csv():
	pass

def transkribus_indices_to_koha():
	pass


### TEST ####

#transkribus_pages_directory = os.path.join("data", "page_xml")

transkribus_pages_directory = os.path.join("tmp")



#test_page_xml = os.path.join(transkribus_pages_directory, "12D02-1", "12D02-1_002.xml")

test_page_xml = os.path.join(transkribus_pages_directory,"20124691_002.xml")

collection_id = 257292

document_id = 1860507

page_number = 12

relations_spotting_from_page_xml(test_page_xml)

#get_page_xml_transkribus_api(collection_id,document_id,page_number)

post_page_xml_transkribus_api(collection_id,document_id,page_number,test_page_xml.replace(".xml","_with_relations.xml"))

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

#import_transkribus_tk_indices()