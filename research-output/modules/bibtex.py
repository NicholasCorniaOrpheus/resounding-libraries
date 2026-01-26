import sys

sys.path.append("./modules")

from modules.utilities import *
from modules.koha import *

from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase

import re

### TESTING

bibtex_string = r"""
@inproceedings{cornia_whos_2024,
	address = {San Francisco, USA},
	title = {Who's {Afraid} of the {Artyfyshall} {Byrd}? {Historical} {Notions} and {Current} {Challenges} of {Musical} {Artificiality}},
	url = {https://zenodo.org/records/14877381},
	abstract = {The meteoric surge of AI-generated music has prompted significant concerns among artists and publishers alike. Some fear that the adoption of AI is poised to result in massive job destruction; others sense it will jeopardize and eventually upend all legal frameworks of intellectual property. AI, however, is not the first instance where humanity has confronted the prospect of machines emulating musical creativity. Already in the Baroque, various modes of musical artificiality were explored, ranging from automata and organ stops mimicking human performance and natural sounds, up to devices for mechanized composition (e.g., Athanasius Kircher, Johann Philip Kirnberger, C.P.E. Bach, Antonio Calegari and Diederich Nickolaus Winkel). Valuable insights emerge from the reconsideration—and digital implementation—of these curiosities through the lens of present-day generative models. It can be argued that the very notion of ‘artificiality’ has presented humanity with long-standing philosophical dilemmas, in addressing the debate on the role of art as a substitute of (divine) nature. By digitally implementing and formalizing some pioneering instances of algorithmically-generated music we wish to illustrate how mechanical devices have played a role in human art and entertainment prior to our digital era.},
	language = {en},
	booktitle = {International {Society} for {Music} {Information} {Retrieval} {Conference} ({ISMIR} 2024)},
	author = {Cornia, Nicholas and Forment, Bruno},
	year = {2024},
}
"""
bibtext_entry = {
	"address": "San Francisco, USA",
	"title": "Who's {Afraid} of the {Artyfyshall} {Byrd}? {Historical} {Notions} and {Current} {Challenges} of {Musical} {Artificiality}",
	"url": "https://zenodo.org/records/14877381",
	"abstract": "The meteoric surge of AI-generated music has prompted significant concerns among artists and publishers alike. Some fear that the adoption of AI is poised to result in massive job destruction; others sense it will jeopardize and eventually upend all legal frameworks of intellectual property. AI, however, is not the first instance where humanity has confronted the prospect of machines emulating musical creativity. Already in the Baroque, various modes of musical artificiality were explored, ranging from automata and organ stops mimicking human performance and natural sounds, up to devices for mechanized composition (e.g., Athanasius Kircher, Johann Philip Kirnberger, C.P.E. Bach, Antonio Calegari and Diederich Nickolaus Winkel). Valuable insights emerge from the reconsideration—and digital implementation—of these curiosities through the lens of present-day generative models. It can be argued that the very notion of ‘artificiality’ has presented humanity with long-standing philosophical dilemmas, in addressing the debate on the role of art as a substitute of (divine) nature. By digitally implementing and formalizing some pioneering instances of algorithmically-generated music we wish to illustrate how mechanical devices have played a role in human art and entertainment prior to our digital era.",
	"language": "en",
	"booktitle": "International {Society} for {Music} {Information} {Retrieval} {Conference} ({ISMIR} 2024)",
	"author": "Cornia, Nicholas and Forment, Bruno",
	"year": "2024",
	"ENTRYTYPE": "inproceedings",
	"ID": "cornia_whos_2024",
}

### EXPORTING TO BIBTEX


def parse_entries_to_bibtex(entries, bibtext_filepath):
	# initialize BibTeX database
	bibtext_db = BibDatabase()
	# initialize BibTeX writer
	bibtext_writer = BibTexWriter()

	# add entries to database
	bibtext_db.entries = entries

	with open(bibtext_filepath, "w") as bibfile:
		bibfile.write(bibtext_writer.write(bibtext_db))


### ENTRYTYPES


def generate_researchers_dict(
	research_groups_file,
	participant_field="500",
	participant_name_subfield="a",
	participant_authid_subfield="9",
):
	print("Generating researchers dictionary...")

	# import research groups as dictionary
	research_groups = json2dict(research_groups_file)

	researchers = []

	# get researchers for each participants field
	for item in research_groups:
		# print(f"Current item: {item["name"]}")
		# get authority record from Koha API
		item_marc = get_authority_marc(item["auth_id"])
		participants = list(
			filter(lambda x: participant_field in x.keys(), item_marc["fields"])
		)
		# print(f"Participants: \n {participants}")
		for participant in participants:
			name = list(
				filter(
					lambda x: participant_name_subfield in x.keys(),
					participant[participant_field]["subfields"],
				)
			)[0][participant_name_subfield]
			auth_id = list(
				filter(
					lambda x: participant_authid_subfield in x.keys(),
					participant[participant_field]["subfields"],
				)
			)[0][participant_authid_subfield]
			researchers.append(
				{
					"name": name,
					"auth_id": auth_id,
					"group_name": item["name"],
					"group_auth_id": item["auth_id"],
				}
			)

	# print(researchers)

	return researchers


# given a list of researchers, it returns a series of BibTeX files, according to a given Koha public report
def generate_bibtex_entries(
	researchers,
	bibtext_filepath,
	entries_mapping,
	report_id,
	fields=["biblio_id", "control", "author", "type"],
):
	institute_entries = []

	groups_entries = []

	research_outputs = get_public_report(report_id, fields)

	for researcher in researchers:
		researcher_entries = []
		# generate folders group->researcher:
		if not os.path.exists(os.path.join(bibtext_filepath, researcher["group_name"].split(":")[0].replace(" ","_"))):
			os.makedirs(os.path.join(bibtext_filepath, researcher["group_name"].split(":")[0].replace(" ","_")))
		if not os.path.exists(
			os.path.join(bibtext_filepath, researcher["group_name"].split(":")[0].replace(" ","_"), researcher["name"].replace(" ","_"))
		):
			os.makedirs(
				os.path.join(
					bibtext_filepath, researcher["group_name"].split(":")[0].replace(" ","_"), researcher["name"].replace(" ","_")
				)
			)
		# get output related to current researcher
		researcher_output = list(
			filter(lambda x: x["author"] == researcher["name"], research_outputs)
		)
		# organize the output according to the BibTeX mapping
		for output in researcher_output:
			output_marc = get_biblionumber_marc(output["biblio_id"])
			# map entry type according to output-type
			entrytype = entries_mapping[output["type"]]["bibtex"]
			bibtex_id = f"{output["author"].split(",")[0].replace(" ","_")}_{output["biblio_id"]}"
			if entrytype == "article":
				researcher_entries.append({
					"ENTRYTYPE": entrytype,
					"ID": bibtex_id,
					"author": get_authors(output_marc),
					"title": get_title(output_marc),
					"journal": get_journal(output_marc),
					"year": str(get_year(output_marc)),
					"volume": get_volume(output_marc),
					"number": get_issue_number(output_marc),
					"issn": get_issn(output_marc),
					"pages": get_pages(output_marc),
					"url": get_url(output_marc),
					"doi": get_doi(output_marc),
					"keywords": get_keywords(output_marc),
					"abstract": get_abstract(output_marc),
					"note": get_note(output_marc),
					"type": get_type(output_marc,entries_mapping),
					"howpublished": get_howpublished(output_marc)
					})


			elif entrytype == "book":
				 researcher_entries.append({
					"ENTRYTYPE": entrytype,
					"ID": bibtex_id,
					"author": get_authors(output_marc),
					"title": get_title(output_marc),
					"publisher": get_publisher(output_marc),
					"address": get_address(output_marc),
					"year": str(get_year(output_marc)),
					"isbn": get_isbn(output_marc),
					"pages": get_pages(output_marc),
					"url": get_url(output_marc),
					"doi": get_doi(output_marc),
					"keywords": get_keywords(output_marc),
					"abstract": get_abstract(output_marc),
					"note": get_note(output_marc),
					"type": get_type(output_marc,entries_mapping),
					"howpublished": get_howpublished(output_marc)
					})

			elif entrytype == "incollection":
				 researcher_entries.append({
					"ENTRYTYPE": entrytype,
					"ID": bibtex_id,
					"author": get_authors(output_marc),
					"title": get_title(output_marc),
					"booktitle": get_booktitle(output_marc),
					"publisher": get_publisher(output_marc),
					"address": get_address(output_marc),
					"year": str(get_year(output_marc)),
					"isbn": get_isbn(output_marc),
					"pages": get_pages(output_marc),
					"url": get_url(output_marc),
					"doi": get_doi(output_marc),
					"keywords": get_keywords(output_marc),
					"abstract": get_abstract(output_marc),
					"note": get_note(output_marc),
					"type": get_type(output_marc,entries_mapping),
					"howpublished": get_howpublished(output_marc)
					})

			elif entrytype == "misc":
				 researcher_entries.append({
					"ENTRYTYPE": entrytype,
					"ID": bibtex_id,
					"author": get_authors(output_marc),
					"title": get_title(output_marc),
					"publisher": get_publisher(output_marc),
					"address": get_address(output_marc),
					"year": str(get_year(output_marc)),
					"url": get_url(output_marc),
					"doi": get_doi(output_marc),
					"keywords": get_keywords(output_marc),
					"abstract": get_abstract(output_marc),
					"note": get_note(output_marc),
					"type": get_type(output_marc,entries_mapping),
					"howpublished": get_howpublished(output_marc)
					})

			elif entrytype == "phdthesis":
				 researcher_entries.append({
					"ENTRYTYPE": entrytype,
					"ID": bibtex_id,
					"author": get_authors(output_marc),
					"title": get_title(output_marc),
					"school": get_school(output_marc),
					"address": get_address(output_marc),
					"year": str(get_year(output_marc)),
					"pages": get_pages(output_marc),
					"url": get_url(output_marc),
					"doi": get_doi(output_marc),
					"keywords": get_keywords(output_marc),
					"abstract": get_abstract(output_marc),
					"note": get_note(output_marc),
					"type": get_type(output_marc,entries_mapping),
					"howpublished": get_howpublished(output_marc)
					})
			else:
				print(f"Error: no entrytype found for biblio_id {output["biblio_id"]}")
				pass

			# generate single bibtex file
			single_bibtex_db = BibDatabase()
			# initialize BibTeX writer
			single_bibtex_writer = BibTexWriter()

			# add entries to database
			single_bibtex_db.entries = [researcher_entries[-1]]

			filepath = os.path.join(bibtext_filepath,researcher["group_name"].split(":")[0].replace(" ","_"),researcher["name"].replace(" ","_"),f"{researcher_entries[-1]["ID"]}.bib")

			with open(filepath, "w") as bibfile:
				bibfile.write(single_bibtex_writer.write(single_bibtex_db))


		# generate BibTex for researcher
		bibtex_db = BibDatabase()
		# initialize BibTeX writer
		bibtex_writer = BibTexWriter()
		bibtex_db.entries = researcher_entries
		filepath = os.path.join(bibtext_filepath,researcher["group_name"].split(":")[0].replace(" ","_"),researcher["name"].replace(" ","_"),f"{researcher["name"].replace(" ","_")}_full_output.bib")

		with open(filepath, "w") as bibfile:
			bibfile.write(bibtex_writer.write(bibtex_db))


		# TO BE CONTINUED

		"""
		- make groups and institute entries
		- generate bibtex files for each level, and create single entries for researchers.

		"""




## LaTex special characters normalization


def latex_normalize(input_string):
	special_chars = {
		"&": r"\&",
		"%": r"\%",
		"$": r"\$",
		"#": r"\#",
		"_": r"\_",
		"{": r"\{",
		"}": r"\}",
		"~": r"\textasciitilde{}",
		"^": r"\^{}",
		"\\": r"\textbackslash{}",
	}

	pattern = re.compile("|".join(re.escape(key) for key in special_chars.keys()))
	normalized_string = pattern.sub(lambda x: special_chars[x.group()], input_string)

	return normalized_string


# CONVERT FUNCTIONS MARC2BIBTEX

### I am assuming a record as marc-in-json format

def get_abstract(record_dict,field="520",subfield="a"):
	abstract = ""

	filter_query = list(filter(lambda x: field in x.keys(), record_dict["fields"]))

	if len(filter_query) > 0:
		subfield_query = list(
			filter(lambda x: subfield in x.keys(), filter_query[0][field]["subfields"])
		)
		if len(subfield_query) > 0:
			abstract = subfield_query[0][subfield]

	return abstract


country_codes = csv2dict(os.path.join("mappings","country_codes.csv"))

country_acronyms = {}

for country in country_codes:
	country_acronyms[country["code"]] = country["label"]


def get_address(record_dict,field="260",subfield="a",country_field="044",country_subfield="a",acronyms_mapping=country_acronyms):
	address = ""

	filter_query = list(filter(lambda x: field in x.keys(), record_dict["fields"]))

	if len(filter_query) > 0:
		subfield_query = list(
			filter(lambda x: subfield in x.keys(), filter_query[0][field]["subfields"])
		)
		if len(subfield_query) > 0:
			address = subfield_query[0][subfield]

		else: # case of country of publication field 044$a
			filter_query = list(filter(lambda x: country_field in x.keys(), record_dict["fields"]))

			if len(filter_query) > 0:
				subfield_query = list(
					filter(lambda x: subfield in x.keys(), filter_query[0][country_field]["subfields"])
				)
				if len(subfield_query) > 0:
					address = acronyms_mapping[subfield_query[0][country_subfield]]


	return address

role_codes = csv2dict(os.path.join("mappings","role_codes.csv"))

role_acronyms = {}

for role in role_codes:
	role_acronyms[role["code"]] = role["label"]


def get_authors(record_dict, main_field="100", main_subfield="a", alt_field="700", alt_subfield = "a", role_subfield="4", acronyms_mapping=role_acronyms,roles=False):
	author_list = []
	
	if roles is not True:
		# get main author
		filter_query = list(filter(lambda x: main_field in x.keys(), record_dict["fields"]))

		if len(filter_query) > 0:
			for entry in filter_query:
				subfield_query = list(
					filter(lambda x: main_subfield in x.keys(), entry[main_field]["subfields"])
				)
				if len(subfield_query) > 0:
					author_list.append(subfield_query[0][main_subfield])

		# get additional authors
		filter_query = list(filter(lambda x: alt_field in x.keys(), record_dict["fields"]))

		if len(filter_query) > 0:
			for entry in filter_query:
				subfield_query = list(
					filter(lambda x: alt_subfield in x.keys(), entry[alt_field]["subfields"])
				)
				if len(subfield_query) > 0:
					author_list.append(subfield_query[0][alt_subfield])
	else:
		# get main author
		filter_query = list(filter(lambda x: main_field in x.keys(), record_dict["fields"]))

		if len(filter_query) > 0:
			for entry in filter_query:
				subfield_query = list(
					filter(lambda x: main_subfield in x.keys(), entry[main_field]["subfields"])
				)
				if len(subfield_query) > 0:
					author_list.append(f"{subfield_query[0][main_subfield]} ({acronyms_mapping[subfield_query[0][role_subfield]]})")

		# get additional authors
		filter_query = list(filter(lambda x: alt_field in x.keys(), record_dict["fields"]))

		if len(filter_query) > 0:
			for entry in filter_query:
				subfield_query = list(
					filter(lambda x: alt_subfield in x.keys(), entry[alt_field]["subfields"])
				)
				if len(subfield_query) > 0:
					author_list.append(f"{subfield_query[0][alt_subfield]} ({acronyms_mapping[subfield_query[0][role_subfield]]})")


	# parse authors in one string
	return " and ".join(author_list)

def get_howpublished(record_dict, license_field="506", licence_subfield="a", referee_field="591", referee_subfield="a", acronyms_mapping= {"0": "Not peer-reviewed", "1": "Peer-reviewed", "Editorial review": "Peer-reviewed" }):
	howpublished = ""

	# License information
	filter_query = list(filter(lambda x: license_field in x.keys(), record_dict["fields"]))

	if len(filter_query) > 0:
		subfield_query = list(
			filter(lambda x: licence_subfield in x.keys(), filter_query[0][license_field]["subfields"])
		)
		if len(subfield_query) > 0:
			howpublished = subfield_query[0][licence_subfield]

	# Referee information

	filter_query = list(filter(lambda x: referee_field in x.keys(), record_dict["fields"]))

	if len(filter_query) > 0:
		subfield_query = list(
			filter(lambda x: referee_subfield in x.keys(), filter_query[0][referee_field]["subfields"])
		)
		if len(subfield_query) > 0:
			howpublished += f", {acronyms_mapping[subfield_query[0][referee_subfield]]}"
			

	return howpublished


def get_booktitle(record_dict, field="773", subfield="t"):
	booktitle = ""

	filter_query = list(filter(lambda x: field in x.keys(), record_dict["fields"]))

	if len(filter_query) > 0:
		subfield_query = list(
			filter(lambda x: subfield in x.keys(), filter_query[0][field]["subfields"])
		)
		if len(subfield_query) > 0:
			booktitle = subfield_query[0][subfield]

	return booktitle


def get_doi(
	record_dict,
	field="856",
	subfield="u",
	control_field="856",
	control_subfield="3",
	control_value="DOI",
):
	doi = ""

	filter_query = list(filter(lambda x: field in x.keys(), record_dict["fields"]))
	if len(filter_query) > 0:
		for entry in filter_query:
			control_subfield_query = list(
				filter(lambda x: control_subfield in x.keys(), entry[control_field]["subfields"])
			)
			if len(control_subfield_query) > 0:
				if control_subfield_query[0][control_subfield] == control_value:
					subfield_query = list(
						filter(lambda x: subfield in x.keys(), entry[field]["subfields"])
					)
					if len(subfield_query) > 0:
						doi = latex_normalize(subfield_query[0][subfield]).replace(
							"https://doi.org/", ""
						)

	return doi


def get_institution(
	record_dict, field="610", subfield="a", main_institution="Orpheus Instituut"
):
	institution = ""

	filter_query = list(filter(lambda x: field in x.keys(), record_dict["fields"]))

	if len(filter_query) > 0:
		subfield_query = list(
			filter(lambda x: subfield in x.keys(), filter_query[0][field]["subfields"])
		)
		if len(subfield_query) > 0:
			institution = subfield_query[0][subfield]

	return institution


def get_issn(record_dict, field="773", subfield="x"):
	issn = ""

	filter_query = list(filter(lambda x: field in x.keys(), record_dict["fields"]))

	if len(filter_query) > 0:
		subfield_query = list(
			filter(lambda x: subfield in x.keys(), filter_query[0][field]["subfields"])
		)
		if len(subfield_query) > 0:
			issn = subfield_query[0][subfield].replace("-", "")

	return issn


def get_isbn(record_dict, field="773", subfield="z"):
	isbn = ""

	filter_query = list(filter(lambda x: field in x.keys(), record_dict["fields"]))

	if len(filter_query) > 0:
		subfield_query = list(
			filter(lambda x: subfield in x.keys(), filter_query[0][field]["subfields"])
		)
		if len(subfield_query) > 0:
			isbn = subfield_query[0][subfield].replace("-", "")

	return isbn


def get_journal(record_dict, field="773", subfield="t"):
	journal = ""

	filter_query = list(filter(lambda x: field in x.keys(), record_dict["fields"]))

	if len(filter_query) > 0:
		subfield_query = list(
			filter(lambda x: subfield in x.keys(), filter_query[0][field]["subfields"])
		)
		if len(subfield_query) > 0:
			journal = subfield_query[0][subfield]

	return journal

def get_keywords(record_dict, field="650", subfield="a"):
	keywords_list = []

	filter_query = list(filter(lambda x: field in x.keys(), record_dict["fields"]))

	if len(filter_query) > 0:
		for entry in filter_query:
			subfield_query = list(
				filter(lambda x: subfield in x.keys(), entry[field]["subfields"])
			)
			if len(subfield_query) > 0:
				keywords_list.append(subfield_query[0][subfield])

	# parse keywords in one string
	return ", ".join(keywords_list)

def get_note(record_dict, field="500", subfield="a"):
	note = ""

	filter_query = list(filter(lambda x: field in x.keys(), record_dict["fields"]))

	if len(filter_query) > 0:
		subfield_query = list(
			filter(lambda x: subfield in x.keys(), filter_query[0][field]["subfields"])
		)
		if len(subfield_query) > 0:
			note = subfield_query[0][subfield]

	return note

def get_issue_number(record_dict, field="773", subfield="g"):
	issue_number = ""

	filter_query = list(filter(lambda x: field in x.keys(), record_dict["fields"]))

	if len(filter_query) > 0:
		subfield_query = list(
			filter(lambda x: subfield in x.keys(), filter_query[0][field]["subfields"])
		)
		if len(subfield_query) > 0:
			# check if there are multiple informations, such as volume and issue.
			comma_sep = subfield_query[0][subfield].split(",")
			if len(comma_sep) == 1:  # only pages case
				pass

			else:  # volume,issue,pages case
				issue_number = comma_sep[1].replace(" ","")

	return issue_number



def get_pages(record_dict, field="773", subfield="g"):
	pages = ""

	filter_query = list(filter(lambda x: field in x.keys(), record_dict["fields"]))

	if len(filter_query) > 0:
		subfield_query = list(
			filter(lambda x: subfield in x.keys(), filter_query[0][field]["subfields"])
		)
		if len(subfield_query) > 0:
			# check if there are multiple informations, such as volume and issue.
			comma_sep = subfield_query[0][subfield].split(",")
			if len(comma_sep) == 1:  # only pages case
				pages = comma_sep[0].replace("-", "--").replace(" ","")

			else:  # volume,issue,pages case
				pages = comma_sep[2].replace("-", "--").replace(" ","")

	return pages

def get_publisher(record_dict,field="260",subfield="b"):
	publisher = ""

	filter_query = list(filter(lambda x: field in x.keys(), record_dict["fields"]))

	if len(filter_query) > 0:
		subfield_query = list(
			filter(lambda x: subfield in x.keys(), filter_query[0][field]["subfields"])
		)
		if len(subfield_query) > 0:
			publisher = subfield_query[0][subfield]

	return publisher

def get_school(record_dict,field="260",subfield="b"):
	school = ""

	filter_query = list(filter(lambda x: field in x.keys(), record_dict["fields"]))

	if len(filter_query) > 0:
		subfield_query = list(
			filter(lambda x: subfield in x.keys(), filter_query[0][field]["subfields"])
		)
		if len(subfield_query) > 0:
			school = subfield_query[0][subfield]

	return school


def get_type(record_dict,entries_mapping,field="942",subfield="c"):
	type = ""

	filter_query = list(filter(lambda x: field in x.keys(), record_dict["fields"]))

	if len(filter_query) > 0:
		subfield_query = list(
			filter(lambda x: subfield in x.keys(), filter_query[0][field]["subfields"])
		)
		if len(subfield_query) > 0:
			type = subfield_query[0][subfield]
			type = entries_mapping[type]["koha"]

	return type

def get_title(record_dict,field="245",subfield="a"):
	title = ""

	filter_query = list(filter(lambda x: field in x.keys(), record_dict["fields"]))

	if len(filter_query) > 0:
		subfield_query = list(
			filter(lambda x: subfield in x.keys(), filter_query[0][field]["subfields"])
		)
		if len(subfield_query) > 0:
			title = subfield_query[0][subfield]

	return title

def get_url(
	record_dict,
	field="856",
	subfield="u",
	control_field="856",
	control_subfield="3",
	control_value="Universal Resource Locator",
):
	url = ""

	filter_query = list(filter(lambda x: field in x.keys(), record_dict["fields"]))
	if len(filter_query) > 0:
		for entry in filter_query:
			control_subfield_query = list(
				filter(lambda x: control_subfield in x.keys(), entry[field]["subfields"])
			)
			if len(control_subfield_query) > 0:
				if control_subfield_query[0][control_subfield] == control_value:
					subfield_query = list(
						filter(lambda x: subfield in x.keys(), entry[field]["subfields"])
					)
					if len(subfield_query) > 0:
						url = subfield_query[0][subfield]
						

	return url

def get_volume(record_dict, field="773", subfield="g"):
	volume = ""

	filter_query = list(filter(lambda x: field in x.keys(), record_dict["fields"]))

	if len(filter_query) > 0:
		subfield_query = list(
			filter(lambda x: subfield in x.keys(), filter_query[0][field]["subfields"])
		)
		if len(subfield_query) > 0:
			# check if there are multiple informations, such as volume and issue.
			comma_sep = subfield_query[0][subfield].split(",")
			if len(comma_sep) == 1:  # only pages case
				pass

			else:  # volume,issue,pages case
				volume = comma_sep[0]

	return volume

def get_year(record_dict, fields=[["502","a"],["336","b"],["260","c"]]):
	year = ""

	for field in fields:

		filter_query = list(filter(lambda x: field[0] in x.keys(), record_dict["fields"]))

		if len(filter_query) > 0:
			subfield_query = list(
				filter(lambda x: field[1] in x.keys(), filter_query[0][field[0]]["subfields"])
			)
			if len(subfield_query) > 0:
				# found date of publication in the format yyyy-mm-dd
				year = subfield_query[0][field[1]].split("-")[0]
				return year

