import sys

sys.path.append(".")
from utilities import *
from api import *

# Wikibase API and SPARQL endpoint modules
from wikibaseintegrator import wbi_login, WikibaseIntegrator
from wikibaseintegrator.wbi_config import config as wbi_config
from SPARQLWrapper import SPARQLWrapper, JSON

# Set User Agent
wbi_config[
    "USER_AGENT"
] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11"
wb = WikibaseIntegrator()


# TOO MANY authorities... not working.
def get_authorities_number_via_koha_report(mapping_reports_path, report_id, public_report_url):
    # get report mapping
    print("Getting mapping for reports...")
    reports = json2dict(mapping_reports_path)
    query = list(filter(lambda x: x["id"] == report_id, reports))
    if len(query) > 0:
        reportfields = query[0]
    else:
        print("Report ID not found")
        return []

    print(f"Report id = {query[0]["id"]}")

    print(f"API call: {public_report_url + str(report_id)}")

    # convert API report according to mapping and return dictionary
    response = requests.get(public_report_url + str(report_id))
    #print(f"Response: {response.text}")
    results = response.json()
    #print(f"Results: {results}")
    pretty_results = []
    for result in results:
        pretty_result = {}
        for i in range(len(result)):
            pretty_result[reportfields["fields"][i]] = result[i]

        pretty_results.append(pretty_result)

    print(f"Example result: {pretty_results[0]}")

    return pretty_results

def generate_authority_dict_from_api(mapping_reports_path, report_id, public_report_url):

	#get maximal authority number from report
	max_auth_id = get_authorities_number_via_koha_report(mapping_reports_path, report_id, public_report_url)[0]["max_authority"]

	print(f"Max authority id: {max_auth_id}")

	auth_dict = []
	for i in range(max_auth_id):
		try:
			#print(f"Current record: {i+1}")
			#print("Getting metadata from API...")
			record = get_authority_marc(i+1)
			#print(f"Retrieved authority: {record}")
			auth_id = record["fields"][0]["001"]
			# add wikidata number, if possible
			query = list(filter(lambda x: "024" in x.keys(), record["fields"] ))

			if len(query) >0:
				for result in query:
					uri_subfield = list(filter(lambda x: "1" in x.keys(), result["024"]["subfields"]))
					if len(uri_subfield) >0 :
						if "wikidata" in uri_subfield[0]["1"]:
							try:
								wd_id = int(uri_subfield[0]["1"].split("/")[-1].replace("Q",""))
							except ValueError:
								try:
									# get value from subfield $a
									qid_subfield = list(filter(lambda x: "a" in x.keys(), result["024"]["subfields"]))[0]["a"]
									w_id = int(qid_subfield.replace("Q",""))
								except Exception:
									wd_id = 0

							break
			else:
				wd_id = 0


			# append results to dictionary
			auth_dict.append({"auth_id": auth_id,"wd_id": wd_id, "record": record})

			#print(auth_dict[-1])
			#input()


		except Exception:
			print(f"Error importing for id: {i}")



	return auth_dict
			

				



# Static version
def generate_authority_dict_from_marc(records_filename):
	f = open(records_filename, "rb")
	n_authorities = 0
	reader = MARCReader(f)
	auth_dict = []
	for record in reader:
		record_dict = record.as_dict()
		try:
			print(f"Current record: {record_dict["fields"][0]["001"]}")
		except KeyError:
			pass

		# add wikidata number, if possible
		query = list(filter(lambda x: "024" in x.keys(), record_dict["fields"] ))

		if len(query) >0:
			for result in query:
				uri_subfield = list(filter(lambda x: "1" in x.keys(), result["024"]["subfields"]))
				if len(uri_subfield) >0 :
					if "wikidata" in uri_subfield[0]["1"]:
						try:
							wd_id = int(uri_subfield[0]["1"].split("/")[-1].replace("Q",""))
						except ValueError:
							try:
								# get value from subfield $a
								qid_subfield = list(filter(lambda x: "a" in x.keys(), result["024"]["subfields"]))[0]["a"]
								w_id = int(qid_subfield.replace("Q",""))
							except Exception:
								wd_id = 0

						break
		else:
			wd_id = 0
		

		try:
			auth_dict.append({"auth_id": record_dict["fields"][0]["001"], "wd_id": wd_id  ,"record": record_dict})
			n_authorities += 1
		except KeyError:
			pass

	print(f"Imported {n_authorities} authorities from Koha.")	
	return auth_dict


# Query using WikibaseIntegrator
def wb_get_property_data(qid, pid):
    entity = wb.item.get(qid)
    try:
        query = []
        prop_values = entity.claims.get(pid)
        print(f"Property: {pid}")
        for prop_value in prop_values:
            print(prop_value.mainsnak.datavalue["type"])
            if prop_value.mainsnak.datavalue["type"] == "time":
                query.append(prop_value.mainsnak.datavalue["value"]["time"][1:11])
            elif prop_value.mainsnak.datavalue["type"] == "wikibase-entityid":
                query.append(prop_value.mainsnak.datavalue["value"]["id"])
            else:
                # print("value case")
                query.append(prop_value.mainsnak.datavalue["value"])

        return query
    except Exception:
        return [""]
