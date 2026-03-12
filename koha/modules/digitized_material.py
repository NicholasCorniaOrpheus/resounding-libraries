"""
Scripts to interact with digitized records
"""

"""
# TO DO:

- [ ] Import digitized records list form CSV
- [ ] Enrich `reproduction_note` field 533$a
- [ ] Generate biblioitems MARC for import to Koha 

"""

import sys

sys.path.append("./modules")  # importing custom functions in modules
from modules.utilities import *
from modules.marc import *
from modules.api import *

# webscraping and automatic click
from bs4 import BeautifulSoup
from selenium import webdriver # to be continued -> use to activate buttons via click() function.

from copy import deepcopy

# I HAD TO USE HTTP otherwise I get Wrong CSRF token :(
upload_url = "http://koha.orpheusinstituut.be/cgi-bin/koha/tools/upload-cover-image.pl?biblionumber="

# Import credentials, assuming you are running the code from the `koha` directory
credentials = json2dict("../credentials/credentials.json")

oauth_credentials = credentials["koha"]["oauth_credentials"]

basic_credentials = credentials["koha"]["basic_credentials"]

# create Oath2 session
my_session = oauth2_session(
    client_id=oauth_credentials["client_id"],
    client_secret=oauth_credentials["secret_key"],
    base_url=base_url,
)

def generate_thumbs_upload_list(cat_dict,digitization_fields=[{"field": "553","subfield": "a","string": "Digitized by Iguana"},{"field": "856","subfield": "3","string": "Koopman Digital"}]):

	digitized_records = []
	for record in cat_dict:
		for digi_field in digitization_fields:
			digitization_query = list(filter(lambda x: digi_field["field"] in x.keys(),record["record"]["fields"]))

			if len(digitization_query) >0:
				# search subfield
				for digitization in digitization_query:
					digitization_subfield_query = list(filter(lambda x: digi_field["subfield"] in x.keys(),digitization[digi_field["field"]]["subfields"]))
					for subfield in digitization_subfield_query:
						if subfield[digi_field["subfield"]] == digi_field["string"]:
							# found it!
							digitized_records.append(record)



def get_CSRF_token_from_URL(url):

	response = my_session.get(url)

	html = response.text 

	#print(html)

	soup = BeautifulSoup(html,'html.parser')

	csrf_token = soup.find('input',attrs={"name": "csrf_token"})["value"]

	return csrf_token

def upload_image_to_record(img_path,biblio_item,session,upload_url):

	# STILL NOT WORKING 
	
	url = f"{upload_url}{biblio_item}"

	csrf_token = get_CSRF_token_from_URL(url)

	print(f"Retrieved CSRF token: {csrf_token}")

	with open(img_path,'rb') as file:
		print(f"Uploading {img_path} via URL: {url} ")
		# The Login is not working properly...
		response = my_session.post(url, data={"csrf-token": csrf_token, "login_user": basic_credentials["user"], "password": basic_credentials["password"] }, files={"file": file})
		print(response.text[:1000])


### NOT WORKING!


def reproduction_note_tag2marc(
	reader, digitized_records_filepath, digitized_barcodes_list, note
):  # returns a MARC file for import to koha
	# inizialize empty file for new MARC records
	#print(f"Sample digitized barcodes list: {digitized_barcodes_list[0:10]}")
	num_digitized_barcodes = len(digitized_barcodes_list)
	digitized_records = open(digitized_records_filepath, "wb")
	counter_records = 0
	for record in reader:
		# collect item barcodes of the record stored in field 952$p
		items_barcodes = []
		for field in record.get_fields("952"):
			try:
				items_barcodes.append(field["p"])
			except Exception:
				pass      
		#print(f"Current items barcodes: {items_barcodes}")
		# check if any of the item barcodes is in the digitized list
		found = False
		for item in items_barcodes:
			if item in digitized_barcodes_list:
				found = True
				counter_records +=1
				digitized_barcodes_list.remove(item)

		if found:
			print(f"Adding reproduction note to biblioitem {record["001"]}...")
			new_record = deepcopy(record)
			# add 533 reproduction note
			new_record.add_field(
				Field(
					tag="533",
					indicators=[" ", " "],
					subfields=[Subfield(code="a",value=note)],
				)
			)
			digitized_records.write(new_record.as_marc())
			# remove barcode from list
		


	print(f"Added {counter_records} to MARC import file from {num_digitized_barcodes}")
	print(f"Unmatched barcodes {len(digitized_barcodes_list)} will be printed in log file")
	# print residual list to .txt file
	logfile = open(digitized_records_filepath[:-4] + "_log.txt", "w+")
	for barcode in digitized_barcodes_list:
		logfile.write(barcode + "\n")

	# save new marc file
	digitized_records.close()
	print_mrc_file(digitized_records_filepath)



