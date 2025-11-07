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

from copy import deepcopy


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
