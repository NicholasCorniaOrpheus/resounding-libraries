'''
Reports scripts
'''

import sys
import os
import requests
sys.path.append("./modules")  # importing custom functions in modules
from modules.utilities import *

data_dir = "./data/"

def report2json(public_report_url,report_id):
	# we are assuming you run the script from the `koha` folder
	reports = json2dict(os.path.join(data_dir,"reports.json"))
	# get report fields according to id
	query = list(filter(lambda x: x["id"] == report_id,reports))
	if len(query) > 0 :
		reportfields = query[0]
	else:
		print("Report ID not found")
		return []

	# convert response into JSON
	response = requests.get(public_report_url+"id="+str(report_id))
	results = response.json()
	pretty_results = []
	for result in results:
		pretty_result = {}
		for i in range(len(result)):
			pretty_result[reportfields["fields"][i]] = result[i]

		pretty_results.append(pretty_result)

	# export result in data folder
	output_filename = os.path.join(data_dir,"reports",f"{get_current_date()}_{reportfields["name"]}.json")
	dict2json(pretty_results,output_filename)


		





'''takes the report n.71 from Koha and cleans it up for Resourcespace
in the form of a dictionary such that:
- barcodes are collated to biblioitem
- contributors are spearated
'''

def koha_biblioitems2json(public_report_url,report_id):
	# import latest catalogue via report
	report2json(public_report_url,report_id)
	koha_report_filename = get_latest_file(os.path.join(data_dir,"reports"))
	koha_report = json2dict(koha_report_filename)
	# create a new list of biblioitems for Resourcespace
	rs_biblios = []
	for element in koha_report:
		if element["biblionumber"] == None:
			pass 
		else:
			# query biblionumber in rs_biblios
			query = list(filter(lambda x: x["biblionumber"] == element["biblionumber"],rs_biblios))
			if len(query)>0:
				# append barcode to existing biblioitem
				print("biblionumber already present:",element)
				input()

			else:
				# split contributors
				element["contributors"] = element["contributors"].split("|")
				while '' in element["contributors"]:
					element["contributors"].remove('')
				# create new biblioitem entry in list 
				rs_biblios.append(element)


	dict2json(rs_biblios,os.path.join(data_dir,"resourcespace","rs_biblios.json"))

