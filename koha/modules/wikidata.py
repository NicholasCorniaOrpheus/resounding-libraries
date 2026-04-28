import sys

sys.path.append(".")
from utilities import *
from api import *

# Statistics
import statistics as stat
#from collections import Counter

# Wikibase API and SPARQL endpoint modules
from wikibaseintegrator import wbi_login, WikibaseIntegrator
from wikibaseintegrator.wbi_config import config as wbi_config
from SPARQLWrapper import SPARQLWrapper, JSON

# Bisect algorithm for logarithmic search
from bisect import bisect_left

# Multiprocessing
from multiprocessing import Pool,cpu_count
from typing import List, Dict, Any
import traceback

# Set User Agent and credential

# Import credentials, assuming you are running the code from the `koha` directory
credentials = json2dict("../credentials/credentials.json")

wikidata_user = credentials["wikidata"]["user"]
wikidata_password = credentials["wikidata"]["password"]

user_agent = credentials["koha"]["oauth_credentials"]["user_agent"]

wbi_config[
	"USER_AGENT"
] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11"

login_instance = wbi_login.Clientlogin(user=wikidata_user, password=wikidata_password)

wb = WikibaseIntegrator(login=login_instance)


def extract_wikidata_id(record):

	query = list(filter(lambda x: "024" in x.keys(), record["fields"] ))
	wd_id = []
	if len(query) >0:
		for result in query:
			uri_subfield = list(filter(lambda x: "1" in x.keys(), result["024"]["subfields"]))
			if len(uri_subfield) >0 :
				if "wikidata" in uri_subfield[0]["1"]:
					try:
						wd_id.append(int(uri_subfield[0]["1"].split("/")[-1].replace("Q","")))
					except ValueError:
						try:
							# get value from subfield $a
							qid_subfield = list(filter(lambda x: "a" in x.keys(), result["024"]["subfields"]))[0]["a"]
							w_id.append(int(qid_subfield.replace("Q","")))
						except Exception:
							pass


	return wd_id

def get_authorities_number_via_koha_report(mapping_reports_path, report_id, public_report_url,user_agent=oauth_credentials["user_agent"]):
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

    # Make the request with User-Agent header
    # Make sure User-Agent is always set
    headers = {
        "User-Agent": user_agent if user_agent not in ["", None] else "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    }

    print(f"Headers: {headers}")
    
    try:
        response = requests.get(public_report_url + str(report_id), headers=headers, timeout=10)
        
        print("REQUEST URL:", response.request.url)
        print("REQUEST HEADERS:", response.request.headers)
        print("REQUEST BODY (bytes):", response.request.body)
        print("STATUS:", response.status_code)
        print("RESPONSE HEADERS:", response.headers)
        print(f"Response text (first 500 chars): {response.text[:500]}")
        
        # Check if response is actually JSON
        if response.headers.get('content-type', '').startswith('application/json'):
            results = response.json()
        else:
            print(f"ERROR: Response is not JSON! Content-Type: {response.headers.get('content-type')}")
            print(f"Full response: {response.text}")
            return []
        
        pretty_results = []
        for result in results:
            pretty_result = {}
            for i in range(len(result)):
                pretty_result[reportfields["fields"][i]] = result[i]
            pretty_results.append(pretty_result)

        print(f"Example result: {pretty_results[0]}")
        return pretty_results
        
    except Exception as e:
        print(f"Request failed with error: {e}")
        import traceback
        traceback.print_exc()
        return []


# MADE BY COPILOT
def fetch_and_process_authority(auth_id: int) -> Dict[str, Any]:
	"""
	Fetch a single authority from API and extract metadata.
	This function runs in parallel worker processes.
	"""
	try:
		record = get_authority_marc(auth_id)
		
		# Extract auth_id from record
		auth_id_value = list(filter(lambda x: "001" in x.keys(),record["fields"]))[0]["001"]
		
		# Extract Wikidata ID
		wd_id = extract_wikidata_id(record)
		
		return {
			"auth_id": auth_id_value,
			"wd_id": wd_id,
			"record": record,
			"success": True
		}
	except Exception as e:
		#print(f"Error importing for id: {auth_id}")
		#print(traceback.format_exc())
		return {
			"auth_id": auth_id,
			"wd_id": [],
			"record": None,
			"success": False,
			"error": str(e)
		}

# MADE BY COPILOT
def generate_authority_dict_from_api_parallel(
	mapping_reports_path, 
	report_id, 
	public_report_url,
	num_workers: int = None
) -> List[Dict[str, Any]]:
	"""
	Generate authority dictionary using parallel processing.
	
	Args:
		mapping_reports_path: Path to mapping reports
		report_id: Report ID
		public_report_url: URL to public report
		num_workers: Number of parallel workers (default: CPU count)
	
	Returns:
		List of authority dictionaries with auth_id, wd_id, and record
	"""
	
	start_time = time()

	# Get max authority number
	max_auth_id = get_authorities_number_via_koha_report(
		mapping_reports_path, 
		report_id, 
		public_report_url
	)[0]["max_authority"]
	
	print(f"Max authority id: {max_auth_id}")
	
	# Set number of workers (default: number of CPU cores)
	if num_workers is None:
		num_workers = max(1, cpu_count() - 1)  # Leave one core free
	
	print(f"Using {num_workers} parallel workers")
	
	# Create range of authority IDs to fetch (1-indexed)
	authority_ids = range(1, max_auth_id + 1)
	
	# Use Pool for parallel processing
	with Pool(num_workers) as pool:
		# Map function across all authority IDs
		results = pool.map(fetch_and_process_authority, authority_ids)
	
	# Filter successful results
	auth_dict = [result for result in results if result["success"]]
	
	print(f"Successfully imported {len(auth_dict)} authorities out of {max_auth_id} in {float(time()-start_time)/60} seconds.")
	
	return auth_dict



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
			wd_id = extract_wikidata_id_from_authority(record)
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
			auth_id = list(filter(lambda x: "001" in x.keys(),record_dict["fields"]))[0]["001"]
			print(f"Current record: {auth_id}")
		except AttributeError:
			auth_id = "0"
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
			auth_dict.append({"auth_id": auth_id, "wd_id": wd_id  ,"record": record_dict})
			n_authorities += 1
		except KeyError:
			pass

	print(f"Imported {n_authorities} authorities from Koha.")	
	return auth_dict

# Enhance authorities via a pre-defined mapping between authority types and Wikidata properties
def enhance_authorities_via_wikidata(auth_dict,qid_log_dir,wikidata_koha_mapping,batch_modifications_dir,in_progress=False,exclude_types=["KOOPM_KEYW"],koha_fields={"PERSO_NAME": "500","CORPO_NAME": "510","CHRON_TERM": "548","TOPIC_TERM": "550","GEOGR_NAME": "551"}):

	headings = {"PERSO_NAME": "100","CORPO_NAME": "110","CHRON_TERM": "148","TOPIC_TERM": "150","GEOGR_NAME": "151"}

	n_authorities = len(auth_dict)

	current_auth = 0
	if in_progress is not True:
		backup_authorities = []
		changed_authorities = []
		qid_log = []
	else:
		# get latest backup and changed
		print(f"Importing latest backup, changed and qid_log dictionaries...")
		backup_authorities = json2dict(get_latest_file(os.path.join(batch_modifications_dir,"backup")))
		changed_authorities = json2dict(get_latest_file(os.path.join(batch_modifications_dir,"changed")))   
		qid_log = csv2dict(get_latest_file(qid_log_dir))
		# transform qid_log occurrence field to int
		for entry in qid_log:
			entry["occurrence"] = int(entry["occurrence"])

	print("Sorting authorities according to their QID...")
	auth_dict_sorted_qid,auth_qid_list = generate_qid_sorted_dict_and_list(auth_dict)

	perso_properties = list(filter(lambda x: x["type_source"] == "PERSO_NAME", wikidata_koha_mapping))
	topic_properties = list(filter(lambda x: x["type_source"] == "TOPIC_TERM", wikidata_koha_mapping))
	corpo_properties = list(filter(lambda x: x["type_source"] == "CORPO_NAME", wikidata_koha_mapping))
	chron_properties = list(filter(lambda x: x["type_source"] == "CHRON_TERM", wikidata_koha_mapping))
	geogr_properties = list(filter(lambda x: x["type_source"] == "GEOGR_NAME", wikidata_koha_mapping))
	#biblio_properties = list(filter(lambda x: x["type_source"] == "BIBLIO_NUM", wikidata_koha_mapping))

	backup_counter = 0

	start_time = time()

	print("Enhancing authorities with Wikidata data...")

	last_authority = int(input("Choose a starting authority number:"))


	for auth in auth_dict:
		current_auth +=1
		if int(auth["auth_id"]) < last_authority:
			continue
		else:
			print(f"\n\n####### CURRENT AUTHORITY: {auth["auth_id"]} {float(current_auth)/n_authorities*100}%")
			# check if authority is already in backup_authorities
			if in_progress is True:
				backup_query = list(filter(lambda x: x["auth_id"] == auth["auth_id"], backup_authorities))
				if len(backup_query) > 0:
					print("Authority already processed, skipping...")
					continue

			# exclude if belongs to exclude_types
			auth_type = list(filter(lambda x: "942" in x.keys(), auth["record"]["fields"]))
			try:
				if auth_type[0]["942"]["subfields"][0]["a"] in exclude_types:
					print("Excluding authority from enhancement...")
					continue
			except Exception:
				continue

			backup_auth = deepcopy(auth)
			changed_record = False
			if len(auth["wd_id"]) >0:
				for qid in auth["wd_id"]:
					qid = "Q"+str(qid)
					print(f"QID: {qid}")
					# get wikidata entity associated with authority
					try:
						entity = wb.item.get(qid,max_retries=10,retry_after=5)
					except Exception:
						entity = None
					# get authority type from field 942$a
					auth_type = list(filter(lambda x: "942" in x.keys(), auth["record"]["fields"]))[0]
					auth_type = auth_type["942"]["subfields"][0]["a"]
					# get properties from mapping according to auth_type (source field)
					if auth_type == "PERSO_NAME":
						properties = perso_properties
					elif auth_type == "TOPIC_TERM":
						properties = topic_properties
					elif auth_type == "CORPO_NAME":
						properties = corpo_properties
					elif auth_type == "CHRON_TERM":
						properties = chron_properties
					elif auth_type == "GEOGR_NAME":
						properties = geogr_properties
					else:
						# skip authority from cycle
						continue

					if entity is not None:
						# query Wikidata for each property
						#sleep(1)
						for prop in properties:
							pid = prop["pid"]
							#print(f"CURRENT PROPERTY: {pid}")
							query = wb_get_property_data(entity, pid)
							for value in query:
								if value != "":
									#print(f"Queried value: {value}")
									value_uri = f"http://www.wikidata.org/entity/{value}"
									#1. value is already in authority record, but no $i subfield --> Add value_i_subfield
									# search QID value in authority record field
									try:
										field = koha_fields[prop["type_target"]]
										field_query = list(filter(lambda x: field in x.keys(),auth["record"]["fields"]))

										if len(field_query) > 0: # statement(s) in authority

											for statement in field_query:
												#print(statement)
												#print(statement[field])
												subfield_query = list(filter(lambda x: "1" in x.keys(),statement[field]["subfields"]))
												for subfield_1 in subfield_query:
													if subfield_1["1"] == value_uri:
														# check if $i subfield is already filled
														subfield_i_query = list(filter(lambda x: "i" in x.keys(),statement[field]["subfields"]))
														try:
															if subfield_i_query[0]["i"] != "":
																#2. value is already in authority record, and $i is filled --> skip
																continue
															else:
																#value is already in authority record, but no $i subfield --> Add value_i_subfield
																subfield_i_query[0]["i"] = prop["value_i_subfield"]
																changed_record = True


														except IndexError:
															#value is already in authority record, but no $i subfield --> Add value_i_subfield
															statement[field]["subfields"].append({"i": prop["value_i_subfield"]})
															changed_record = True

										else: # statement not in authority
											# add authority statement, if QID matches an existing authority
											retrieved_authority = retrieve_authority_from_qid(value,auth_qid_list,auth_dict_sorted_qid)
											if retrieved_authority is None:
												print(f"Value {value} not found in Koha thesaurus. Adding it to log list...")
												append_qid_to_qid_log(value,qid_log)
												changed_record = False
											else:
												# value is in the authority
												print(f"Found authority {retrieved_authority["auth_id"]}. Adding it as statement for {auth["auth_id"]}...")
												try:
													retrieved_authority_heading = list(filter(lambda x: headings[prop["type_target"]] in x.keys(), retrieved_authority["record"]["fields"] ))
													retrieved_authority_heading = retrieved_authority_heading[0][headings[prop["type_target"]]]["subfields"][0]["a"]
													#print(retrieved_authority_heading)
													#input()
													print(f"a: {retrieved_authority_heading} \n 9: {retrieved_authority["auth_id"]} \n i: {prop["value_i_subfield"]} ")
													auth["record"]["fields"].append({field: {"ind2": " ","ind1": " ", "subfields": [{"a": retrieved_authority_heading ,"9": retrieved_authority["auth_id"] ,"i": prop["value_i_subfield"] }]}})
													changed_record = True

												except Exception:
													pass

									except KeyError:
										continue


			else:
				continue

			if changed_record:
				backup_authorities.append(backup_auth)
				changed_authorities.append(auth)
				backup_counter +=1
				if backup_counter == 10:
					print("\n\n BACKING UP...")
					# Saving to JSON...
					dict2json(
						backup_authorities,
						os.path.join(
							batch_modifications_dir,"backup", "backup_authorities_wikidata-" + get_current_date() + ".json"
						),
					)
					dict2json(
						changed_authorities,
						os.path.join(
							batch_modifications_dir,"changed", "changed_authorities_wikidata-" + get_current_date() + ".json"
						),
					)
					# Saving to CSV
					dict2csv(qid_log,os.path.join(qid_log_dir,f"qid_log-{get_current_date()}.csv"))

					backup_counter = 0

				#print(f"Changed authority: {changed_authorities[-1]} \n\n")
				#input()


	

	# Saving qid_log
	print(f"Saving QIDs log file to {qid_log_dir}")
	dict2csv(qid_log,os.path.join(qid_log_dir,f"qid_log-{get_current_date()}.csv"))

	print(f"Enhancing completed in {float(time() - start_time)/60} minutes.")

	# return backup and changed_authorities
	return backup_authorities,changed_authorities


def retrieve_auth_id_from_heading(auth_dict,heading):

	headings = {"PERSO_NAME": "100","CORPO_NAME": "110","CHRON_TERM": "148","TOPIC_TERM": "150","GEOGR_NAME": "151"}

	auth_id = None
	print(f"Searching for id for heading {heading} ...")
	#input()
	for auth in auth_dict:
		#print(f"Current id: {auth["auth_id"]}")
		auth_type = list(filter(lambda x: "942" in x.keys(), auth["record"]["fields"]))[0]
		auth_type = auth_type["942"]["subfields"][0]["a"]
		#print(f"authority type: {auth_type}")
		try:
			field = headings[auth_type]
			#print(f"Heading field: {field}")
			auth_heading = list(filter(lambda x: field in x.keys(),auth["record"]["fields"]))[0][field]["subfields"][0]["a"]
			#print(f"authority heading: {auth_heading}")
			if auth_heading == heading:
				auth_id = auth["auth_id"]
				print(f"Found match: return {auth_id}")
				#input()
				break

		except KeyError:
			continue

	return auth_id 


def add_auth_id_in_authority_field(auth_dict,koha_fields={"PERSO_NAME": "500","CORPO_NAME": "510","CHRON_TERM": "548","TOPIC_TERM": "550","GEOGR_NAME": "551"}):
	
	backup_authorities = []
	changed_authorities = []

	for auth in auth_dict:
		print(f"Current authority: {auth["auth_id"]}")
		change_record = False
		for field in koha_fields.keys():
			field_query = list(filter(lambda x: koha_fields[field] in x.keys(),auth["record"]["fields"]))
			for statement in field_query:
				print(statement)
				try:
					subfield_9_query = list(filter(lambda x: "9" in x.keys(),statement[koha_fields[field]]["subfields"]))[0]
					#print(subfield_9_query)
					#input()
					# subfield already filled, skip
					continue 
				except IndexError: # subfield not found
					try:
						auth_id = retrieve_auth_id_from_heading(auth_dict,statement[koha_fields[field]]["subfields"][0]["a"])
						print(f"Retrieved {auth_id} for heading {statement[koha_fields[field]]["subfields"][0]["a"]} ")
						if auth_id != None:
							if change_record == False:
								change_record = True 
								backup_authorities.append(auth)
								statement[koha_fields[field]]["subfields"].append({"9": str(auth_id)})
							else:
								statement[koha_fields[field]]["subfields"].append({"9": str(auth_id)})

					except KeyError:
						print(f"Error for authority {auth["auth_id"]} and field {koha_fields[field]}: subfield $a not found")
						continue
					except IndexError:
						continue 	
		if change_record: # append changed records
			changed_authorities.append(auth)
			#print(f"New record modified: {changed_authorities[-1]}")
			#input()

	return backup_authorities,changed_authorities


def generate_qid_sorted_dict_and_list(auth_dict,exclude_types=["KOOPM_KEYW"]):
	filtered_auth_dict = []
	print(f"Excluding the following authority types: {[auth_type for auth_type in exclude_types]}")
	for auth in auth_dict:
		try:
			auth_type = list(filter(lambda x: "942" in x.keys(), auth["record"]["fields"]))
			if auth_type[0]["942"]["subfields"][0]["a"] not in exclude_types:
				filtered_auth_dict.append(auth)
		except AttributeError:
			continue

	filtered_dict_duplicate_qids = []
	for auth in filtered_auth_dict:
		if len(auth["wd_id"]) == 1:
			# single case
			filtered_dict_duplicate_qids.append({"auth_id": auth["auth_id"], "wd_id": auth["wd_id"][0], "record": auth["record"]})
		elif len(auth["wd_id"]) > 1:
			# multiple qids for authority, duplicate record in list
			for wd_id in auth["wd_id"]:
				filtered_dict_duplicate_qids.append({"auth_id": auth["auth_id"], "wd_id": wd_id, "record": auth["record"]})
		else:
			filtered_dict_duplicate_qids.append({"auth_id": auth["auth_id"], "wd_id": 0, "record": auth["record"]})

	auth_dict_sorted_qid = sorted(filtered_dict_duplicate_qids, key=lambda x: x["wd_id"])
	auth_qid_list = [auth["wd_id"] for auth in auth_dict_sorted_qid]

	print(f"Number of filtered authorities (with multiple QIDs duplicates: {len(auth_dict_sorted_qid)}")

	return auth_dict_sorted_qid, auth_qid_list

# retrieve authority based on QID using bisection algorithm
def retrieve_authority_from_qid(qid,auth_qid_list,auth_dict_sorted_qid):
	try:
		qid = int(qid.replace("Q",""))
		index = bisect_left(auth_qid_list,qid)
		if index != len(auth_qid_list) and auth_qid_list[index] == qid:
			return auth_dict_sorted_qid[index]
		else:
			print(f"Wikidata entity {qid} not found in Koha thesaurus")
			# add to CSV log file

			return None
	except ValueError:
		return None

def append_qid_to_qid_log(qid,qid_log):
	if qid != "":
		# search if qid is already in log
		query_qid = list(filter(lambda x: x["qid"] == qid,qid_log))
		if len(query_qid) > 0:
			# append value
			query_qid[0]["occurrence"] += 1
		else:
			# add new qid to log list
			wd_entity = wb.item.get(qid,max_retries=15,retry_after=10)
			try:
				instance_of = wd_entity.claims.get("P31")[0].mainsnak.datavalue['value']["id"]
			except (IndexError,AttributeError):
				instance_of = ""
			try:
				description = wd_entity.descriptions.get("en").value
			except (IndexError,AttributeError):
				description = ""

			try:
				label = wd_entity.labels.get("en").value
			except (IndexError,AttributeError):
				label = ""
			qid_log.append({"qid": qid, "occurrence": 1,
			 "label": label,
			  "description": description ,
			  "instance_of": instance_of,
			   "uri": "http://wikidata.org/entity/" + qid } 
			   )	

# Query using WikibaseIntegrator
def wb_get_property_data(entity,pid):
	# Generalize to Mathematical Expression (LaTeX), Musica notation (Lilypond), Quantity and Geographical coordinates.
	# add References and Qualifiers.
	try:
		query = []
		prop_values = entity.claims.get(pid)
		#print(f"Property: {pid}")
		for prop_value in prop_values:
			print(prop_value.mainsnak.datavalue["type"])
			if prop_value.mainsnak.datavalue['type'] == "time":
				# converting point in time into yyyy-mm-dd format
				query.append(prop_value.mainsnak.datavalue['value']["time"][1:11])
			elif prop_value.mainsnak.datavalue['type'] == "wikibase-entityid":
				query.append(prop_value.mainsnak.datavalue['value']["id"])
			else:
				# general value case, usually a string or URL
				query.append(prop_value.mainsnak.datavalue['value'])	

		return query
	except Exception:
		return [""]


# Fill in Linked Open Data information to URI in field 024 from a list of external ids mappings
def external_sources_metadata_authorities(auth_dict,external_ids_mapping,uri_field=["024","1"],source_subfield="2",label_subfield="9",id_subfield="a"):
	changed_authorities = []
	backup_authorities = []

	for auth in auth_dict:
		# look for URI field
		backup_auth = deepcopy(auth)
		query_uri_field = list(filter(lambda x: uri_field[0] in x.keys(), auth["record"]["fields"] ))
		if len(query_uri_field) > 0:
			for uri in query_uri_field:
				# get current subfields
				try:
					uri_value = list(filter(lambda x: uri_field[1] in x.keys(), uri[uri_field[0]]["subfields"]))[0][uri_field[1]]
					if uri_value.split("/")[-1] != "": # exclude empty URI, like wikidata.org/entity/
						source_value = list(filter(lambda x: source_subfield in x.keys(), uri[uri_field[0]]["subfields"]))
						label_value = list(filter(lambda x: label_subfield in x.keys(), uri[uri_field[0]]["subfields"]))
						id_value = list(filter(lambda x: id_subfield in x.keys(), uri[uri_field[0]]["subfields"]))
						# if incomplete information
						if any(len(subfield) == 0 for subfield in [source_value,label_value,id_value]):
							# query values from URI
							for external_source in external_ids_mapping:
								if external_source["domain_name"] in uri_value:
									# found source
									# add source
									if len(source_value) > 0:
										source_value[0][source_subfield] = external_source["source"]
									else:
										uri[uri_field[0]]["subfields"].append({source_subfield: external_source["source"]})
									# add identifier
									if len(id_value) > 0:
										id_value[0][id_subfield] = uri_value.split("/")[-1]
									else:
										uri[uri_field[0]]["subfields"].append({id_subfield: uri_value.split("/")[-1]})
									# add label (only wikidata)
									if external_source["source"] == "Wikidata":
										try:
											entity = wb.item.get(uri_value.split("/")[-1])
											try:
												label = entity.labels.get('en').value
												if len(label_value) > 0:
													label_value[0][label_subfield] = label								
												else:
													uri[uri_field[0]]["subfields"].append({label_subfield: label})
											except AttributeError:
												pass
										except ValueError:
											pass

									break

							#print(f"Added source information to {auth["record"]}")
							#input()


							# adding changes
							print(f"Adding changes for {auth["auth_id"]}...")
							backup_authorities.append(backup_auth)
							changed_authorities.append(auth)

				except IndexError:
					continue


	return backup_authorities,changed_authorities





										

# Statistics for Wikidata authority enhancment
def generate_statistics_authorities_wikidata_enhancement(changed_authorities,wikidata_koha_mapping,
	koha_fields={"PERSO_NAME": "500","CORPO_NAME": "510","CHRON_TERM": "548","TOPIC_TERM": "550","GEOGR_NAME": "551"},
	authority_types=["PERSO_NAME","CORPO_NAME","CHRON_TERM","TOPIC_TERM","GEOGR_NAME"]):

	statistics = {"authorities": {"n_changed_authorities": 0, "authority_types": [{auth_type: 0} for auth_type in authority_types] }, "wikidata_properties": [{wd_property["value_i_subfield"]: 0} for wd_property in wikidata_koha_mapping] }

	for auth in changed_authorities:
		statistics["authorities"]["n_changed_authorities"] += 1

		# get authority type
		try:
			auth_type = list(filter(lambda x: "942" in x.keys(), auth["record"]["fields"]))[0]["942"]["subfields"][0]["a"]
		except Exception:
			print(f"{auth["auth_id"]} has malformatted authority type")
			input()

		# increment occurrence of authority type:
		list(filter(lambda x: auth_type in x.keys(),statistics["authorities"]["authority_types"] ))[0][auth_type] +=1

		# count wikidata property statements
		for field in list(koha_fields.values()):
			field_query = list(filter(lambda x: field in x.keys(),auth["record"]["fields"]))
			if len(field_query) > 0 :
				for statement in field_query:
					i_subfield_query = list(filter(lambda x: "i" in x.keys(),statement[field]["subfields"]))
					if len(i_subfield_query) >0:
						wd_property = i_subfield_query[0]["i"]
						# found wikidata property statement, append to statistics
						property_query = list(filter(lambda x: wd_property in x.keys(),statistics["wikidata_properties"]))
						if len(property_query) > 0:
							# append occurence
							property_query[0][wd_property] +=1

		#print(statistics)
		#input()



	return statistics





# Clean up location between parenthesis from main heading, if and only if there is a location statement

def cleanup_parenthesis_location_from_main_heading(
	auth_dict,wikidata_koha_mapping,batch_modifications_dir,
	target_types=["CORPO_NAME","GEOGR_NAME"],
	location_statements=["http://wikidata.org/entity/P17","http://wikidata.org/entity/P361","http://wikidata.org/entity/P131","http://wikidata.org/entity/P159"],
	koha_fields={"PERSO_NAME": "500","CORPO_NAME": "510","CHRON_TERM": "548","TOPIC_TERM": "550","GEOGR_NAME": "551"}
	):

	backup_authorities = []
	changed_authorities = []

	headings = {"PERSO_NAME": "100","CORPO_NAME": "110","CHRON_TERM": "148","TOPIC_TERM": "150","GEOGR_NAME": "151"}

	n_authorities = len(auth_dict)

	current_auth = 0
	
	location_properties = list(filter(lambda x: x["value_i_subfield"]  in location_statements, wikidata_koha_mapping))
	
	backup_counter = 0

	start_time = time()

	print("Cleaning up location within parenthesis from main heading...")

	last_authority = int(input("Choose a starting authority number:"))

	for auth in auth_dict:
		current_auth +=1
		if int(auth["auth_id"]) < last_authority:
			continue
		else:
			print(f"\n\n####### CURRENT AUTHORITY: {auth["auth_id"]} {float(current_auth)/n_authorities*100}%")
			# check if authority is already in backup_authorities
			
			# exclude if not in target_types
			try:
				auth_type = list(filter(lambda x: "942" in x.keys(), auth["record"]["fields"]))[0]["942"]["subfields"][0]["a"]
				try:
					if auth_type in target_types: # authority belongs to the target type
						try:
							main_heading = list(filter(lambda x: headings[auth_type] in x.keys(), auth["record"]["fields"]))[0][headings[auth_type]]["subfields"][0]["a"]
							print(f"Main heading: {main_heading}")

							if "(" in main_heading: # if parenthesis is present
								# check if location statement is present
								print("Parenthesis in main heading...")
								location_value = False
								for statement_field in koha_fields.values():
									# search for i subfield
									statements = list(filter(lambda x: statement_field in x.keys(), auth["record"]["fields"]))
									if len(statements) > 0:
										for s in statements:
											i_subfield = list(filter(lambda x: "i" in x.keys(), s[statement_field]["subfields"]))
											if len(i_subfield) > 0:
												if i_subfield[0]["i"] in location_statements:
													# found statement, add for changing!
													print(f"Found location statement. Removing location in parenthesis from main heading for {auth["auth_id"]}...")
													backup_auth = deepcopy(auth)
													main_heading = main_heading.split("(")[0].strip()
													list(filter(lambda x: headings[auth_type] in x.keys(), auth["record"]["fields"]))[0][headings[auth_type]]["subfields"][0]["a"] = main_heading
													print(f"New main heading: {main_heading}")
													print(f"Authority: {auth}")
													input()
													location_value = True 
													break

								if location_value == True:
									# append to change records
									backup_authorities.append(backup_auth)
									changed_authorities.append(auth)
									backup_counter +=1




						except Exception:
							print(f"Main heading missing for {auth["auth_id"]}")
							continue
					
				except Exception:
					continue
			except Exception:
				continue

			# backup
			if backup_counter == 10:
				print("\n\n BACKING UP...")
				# Saving to JSON...
				dict2json(
					backup_authorities,
					os.path.join(
						batch_modifications_dir,"backup", "backup_authorities_cleanup_main_heading-" + get_current_date() + ".json"
					),
				)
				dict2json(
					changed_authorities,
					os.path.join(
						batch_modifications_dir,"changed", "cleanup_main_heading-" + get_current_date() + ".json"
					),
				)
				

				backup_counter = 0



			





	return backup_authorities,changed_authorities