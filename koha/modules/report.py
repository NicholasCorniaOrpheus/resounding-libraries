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


		


