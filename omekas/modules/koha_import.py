# Scripts for the Koha API and import of metadata

import requests
from requests_oauth2client import OAuth2Client, OAuth2ClientCredentialsAuth

# Bisect algorithm for logarithmic search
from bisect import bisect_left

import sys

sys.path.append("./modules")  # importing custom functions in modules
from modules.utilities import *
from modules.api import *


### KOHA API FUNCTIONS

def oauth2_session(
    client_id: str, client_secret: str, user_agent: str, base_url: str, scope="all"
):
    """Returns an OAuth2 session, given client ID and secret key of your Koha account.

    Args:
                    client_id (str): Client ID associated with your Koha Admin User.
                    client_secret (str): Secret key provided by the Koha Administration.
                    user_agent (str): User-Agent string. Default is None.
                    base_url (str): Base URL for your Koha Staff interface

    Returns:
                    session (oauth2): OAuth2 session

    Examples:
                    >>> my_session = pyreslib.koha.oauth2_session(client_id="{CLIENT_ID}"", client_secret="{SECRET_KEY}" , base_url="https://{KOHA_STAFF_URL}/api/v1")

    """
    token_url = f"{base_url}/oauth/token"  # This may be different for your endpoint

    oauth2client = OAuth2Client(
        token_endpoint=token_url, client_id=client_id, client_secret=client_secret
    )
    # Force the User-Agent before authorization
    if user_agent is not None:
        oauth2client.session.headers.update({"User-Agent": user_agent})
    auth = OAuth2ClientCredentialsAuth(oauth2client, scope=scope, resource=base_url)
    session = requests.Session()
    session.auth = auth
    # And also later, why not?
    if user_agent is not None:
        session.headers.update({"User-Agent": user_agent})
    return session


def get_biblionumber_marc(session, biblio_id: int) -> dict:
    """Get MARC in JSON data for biblionumber from Koha API

    Args:
                    session (oauth2): Oauth2 session provided by `pyreslib.koha.oauth2_session` method.
                    biblio_id (int): Biblio ID for the requested record.

    Returns:
                    response (dict): MARC in JSON serialization of the record.

    Examples:
                    >>> my_session = pyreslib.koha.oauth2_session(client_id="{CLIENT_ID}"", client_secret="{SECRET_KEY}" , base_url="https://{KOHA_STAFF_URL}/api/v1")
                    >>> marc_json_record = pyreslib.koha.get_biblionumber_marc(my_session,12)



    """
    headers = {"Accept": "application/marc-in-json"}
    response = session.get(f"{base_url}/biblios/{str(biblio_id)}", headers=headers)
    return response.json()


#### OMEKA S -- KOHA mapping


def generate_omekas_mapping(mappings_directory:str) -> dict:
    """
    Generates a dictionary from a series of CSV files (auth,biblio,media...).
    Args:
    mappings_directory (str): Path of csv mapping files.
    Returns:
    A dictionary of mappings.
    """
    omekas_mapping = {}

    # get authorities mapping
    omekas_mapping["auth"] = csv2dict(
        os.path.join(mappings_directory, "koha-omekas_mapping - auth.csv")
    )
    # biblio mapping
    omekas_mapping["biblio"] = csv2dict(
        os.path.join(mappings_directory, "koha-omekas_mapping - biblio.csv")
    )
    # get media mapping
    omekas_mapping["media"] = csv2dict(
        os.path.join(mappings_directory, "koha-omekas_mapping - media.csv")
    )
    # get locations
    omekas_mapping["locations"] = csv2dict(
        os.path.join(mappings_directory, "koha-omekas_mapping - locations.csv")
    )
    # get research groups
    omekas_mapping["research_groups"] = csv2dict(
        os.path.join(mappings_directory,"koha-omekas_mapping - research_groups.csv"))

    # get researchers
    omekas_mapping["researchers"] = csv2dict(
        os.path.join(mappings_directory,"koha-omekas_mapping - researchers.csv"))

    # get projects
    omekas_mapping["projects"] = csv2dict(
        os.path.join(mappings_directory,"koha-omekas_mapping - projects.csv"))

    return omekas_mapping

def check_record_presence(record_id: int, omekas_id_list: list) -> int:
    """Check if the record id is already present in Omeka S

    Args:
                record_id (int): Koha Authority or Biblio ID
                omekas_id_list (list): List of ids for bisect search

    Returns:
                index (int): Numerical index of the authority or biblio id if present, **-1** otherwise

    """
    index = bisect_left(omekas_id_list, record_id)
    if index != len(omekas_id_list) and omekas_id_list[index] == record_id:
        return index
    else:
        print(f"Record not present in Omeka S")
        return -1


#### GET BIBLIOITEMS FROM KOHA

def import_digitized_biblioitems_from_koha_api(directories_path: str, biblionumber_barcode_filepath: str, koha_session) -> list:
    """
    Given a directory path, including all digitized items with directory name=barcode, and a list of biblionumbers and their barcodes (from Koha Report), the function returns a list of records in marc-in-json format.
    Args:
    directories_path (str): absolute path of main directory for digitized records.
    biblionumber_barcode_filepath (str): path to Koha CSV report with biblionumber and barcode fields. See SQL query example.
    koha_session: OAuth2 session for Koha API.
    Returns:
    biblioitems (list): list of marc-in-json records from Koha API.

    Examples:
    >>> SQL_query = ""SELECT  items.biblionumber,items.barcode FROM items ORDER BY items.biblionumber"
    >>> biblioitems = import_digitized_biblioitems_from_koha_api(directories_path="import/library_assets", biblionumber_barcode_mapping_file="mappings/biblionumber_barcode.csv", credentials=credentials)
    >>> biblioitems
    >>> [{"leader": ... "fields": [...]... , {"leader": ....}}]
    """
    # import biblionumber_barcode csv
    biblionumber_barcode_list = csv2dict(biblionumber_barcode_filepath)
    # intialize biblioitems output list
    biblioitems = []
    # go through all subdirectories of directories_path
    subdirectories = [ f.path for f in os.scandir(directories_path) if f.is_dir() ]
    for d in subdirectories:
        # match barcode with biblioitem
        print(f"Current directory: {d.name}")
        found = False
        for item in biblionumber_barcode_list:
            if d.name == item["barcode"]:
                biblionumber = int(item["biblionumber"])
                found = True
                break 
        if found is False:
            print(f"Barcode {d.name} not found in Koha catalogue.")
        else:
            print(f"Adding barcode {d.name} to biblioitems with biblionumber {biblionumber}")
            biblioitems.append(get_biblionumber_marc(koha_session,biblionumber))

    return biblioitems
            

def retrieve_koha_omekas_mapping_data(field: str, subfield: str,koha_omekas_mapping:list) -> dict:
    """
    Returns a dictionary with all information regarding the mapping of a specific Koha field$subfield back to Omeka S.
    Args:
    field (str): MARC field as string, such as "024".
    subfield (str): MARC subfield, such as "a".
    koha_omekas_mapping (list): A list of dictionaries providing information in order to apply the conversion between a Koha field to Omeka S payload.
    Returns:
    mapping (dict): A dictionary for the mapping between Koha field and Omeka S payload.

    Examples:
    >>>
    """
    # Retrieve field
    query_field = list(filter(lambda x: x["field"] == field, koha_omekas_mapping))
    # retrieve subfield, assuming this will be unique
    query_subfield = list(filter(lambda x: x["subfield"] == subfield, query_field))

    if len(query_field) == 1:
        return query_subfield[0]
    else:
        print(f"Missing mapping or multiple statements for {field}${subfield}.")
        return None 


def koha_field_to_payload(record: dict,field:str, subfield: str, mapping: dict) -> dict:
    """
    Returns a payload-like dictionary, given a marc-in-json record, koha field and subfield and mapping.
    
    Args:
    record (dict): MARC-in-JSON record of the authority, conform with Koha API.
    field (str): MARC field as string, such as "024".
    subfield (str): MARC subfield, such as "a". Set to `None` if subfield is not needed, such as in the case of "001" field.
    koha_omekas_mapping (dict): A dictionary associated to the field$subfield, providing information in order to apply the conversion between a Koha field to Omeka S payload.

    Returns:
    payload (dict): A playload dictionary, conform to the Omeka S Tools Python package.

    Examples:
    >>> 

    """
    # conform mapping
    # get record information
    payload = []
    query_field = list(filter(lambda x: field in x.keys(), record["fields"]))
    print(query_field)
    if len(query_field) >0:
        if subfield is not None:
            for field_statement in query_field:
                query_subfield = list(filter(lambda x: subfield in x.keys(), field_statement[field]["subdfields"]))
                print(query_subfield)
                # convert according to options and data type
                for subfield_statement in query_subfield:
                    if mapping["data_type"] == 'URI':
                        payload.append({"o:label": subfield_statement[subfield], "id": "" })
                    else:
                        payload.append({"value": subfield_statement[subfield]})

        return payload


        else: # 001 case
            for field_statement in query_field:
                if mapping["data_type"] == "URI":
                    payload.append({"o:label": field_statement[field], "id": "" })
                    
                else: # literal, timestamp, number cases
                    payload.append({"value": field_statement[field] })

                return payload

    else:
        return payload


def convert_biblioitem_to_payload(record: dict, omekas_biblio_list: list, koha_omekas_biblio_dict: dict, credentials: dict, staff=True):
    """Converts a bibliographical record into a payload dictionary, ready to be ingested in Omeka S. **Note**: for now, we convert thesaurus references as URIs, not as Items.
    Args:
                    biblio (dict): a bibliographical record in marc-as-json from Koha API
                    omekas_biblio_list (list): List of biblio ids for bisect search
                    omekas_biblio_dict (dict): A sorted dictionary of Omeka S resources based on Koha biblio number.
                    omekas_mapping (dict): Mapping between Koha fields and Omeka properties
                    credentials (dict): credentials for Omeka S and Koha, including URLs.
                    staff (bool): *True* if you wish to use the Koha Staff URL. Set to *False* for OPAC URL. 

    Returns:
                    payload (dict): a payload dictionary ready to be ingested into Omeka S, according to the mapping.
    """
    if staff:
        koha_auth_url = credentials["koha"]["koha_staff_url"] + "cgi-bin/koha/authorities/detail.pl?authid="
        koha_biblio_url = credentials["koha"]["koha_staff_url"] + "cgi-bin/koha/catalogue/detail.pl?biblionumber="
    else:
        koha_auth_url = credentials["koha"]["koha_opac_url"] + "cgi-bin/koha/opac-authoritiesdetail.pl?authid="
        koha_biblio_url = credentials["koha"]["koha_staff_url"] + "cgi-bin/koha/catalogue/opac-detail.pl?biblionumber="

    # Generate payload of property statements from Koha-Omeka mapping
    payload = {}

    for mapping in omekas_mapping["biblio"]:
        # extract field from auth record
        if mapping["field"] == "001":
            payload[mapping["property"]] = [{"id": f"{koha_biblio_url}{biblio["biblio_id"]}", "label": biblio["biblio_id"]}]
        else:
            field_query = list(
                filter(
                    lambda x: mapping["field"] in x.keys(), biblio["record"]["fields"]
                )
            )
            if len(field_query) > 0:
                for statement in field_query:
                    # get subfield value
                    subfield_query = list(
                        filter(
                            lambda x: mapping["subfield"] in x.keys(),
                            statement[mapping["field"]]["subfields"],
                        )
                    )
                    if len(subfield_query) > 0:
                        if mapping["data_type"] == "Text":
                            try:
                                payload[mapping["property"]].append({"value": subfield_query[0][mapping["subfield"]]})
                            except KeyError: # if the list is not yet made
                                payload[mapping["property"]] = [{"value": subfield_query[0][mapping["subfield"]]}]
                        
                        elif mapping["data_type"] == "URI":
                            try:
                                try:
                                    label = subfield_query[0][mapping["retrieve_label"].split("$")[-1]]
                                except Exception:
                                    print(f"Label for {subfield_query[0]} not found.")
                                    label = "URI"

                                if all([mapping["is_authority"],mapping["is_biblionumber"]]) is False:
                                    payload[mapping["property"]].append({"label": label, "id": subfield_query[0][mapping["subfield"]]})
                                    
                                elif mapping["is_authority"] is True:
                                    payload[mapping["property"]].append({"label": label, "id": f"{koha_auth_url}{subfield_query[0][mapping["subfield"]]}" })

                                elif mapping["is_biblionumber"] is True:
                                    payload[mapping["property"]].append({"label": label, "id": f"{koha_biblio_url}{subfield_query[0][mapping["subfield"]]}" })


                            except KeyError: # if the list is not yet made
                                try:
                                    label = subfield_query[0][mapping["retrieve_label"].split("$")[-1]]
                                except Exception:
                                    print(f"Label for {subfield_query[0]} not found.")
                                    label = "URI"

                                if all([mapping["is_authority"],mapping["is_biblionumber"]]) is False:
                                    payload[mapping["property"]] = {"label": label, "id": subfield_query[0][mapping["subfield"]]}
                                    
                                elif mapping["is_authority"] is True:
                                    payload[mapping["property"]] = {"label": label, "id": f"{koha_auth_url}{subfield_query[0][mapping["subfield"]]}" }

                                elif mapping["is_biblionumber"] is True:
                                    payload[mapping["property"]].append({"label": label, "id": f"{koha_biblio_url}{subfield_query[0][mapping["subfield"]]}" })




                        # I have decided to not create duplicates for authorities.
                        elif mapping["data_type"] == "Item":
                            input("Not yet supported. I have decided to not create items from Koha authorities yet.")



    return payload
    """Converts an authority into a payload dictionary, ready to be ingested in Omeka S. Note that each Omeka S field should have a unique vocabulary type.
    Args:
    auth (dict): an authority record in marc-as-json from Koha API
    omekas_biblio_list (list): List of biblio ids for bisect search
    koha_omekas_mapping (list): Mapping between Koha fields and Omeka properties
    credentials (dict): credentials for Omeka S and Koha, including URLs.
    staff (bool): *True* if you wish to use the Koha Staff URL. Set to *False* for OPAC URL. 

    Returns:
    payload (dict): a payload dictionary ready to be ingested into Omeka S, according to the mapping.

    """
    # get biblio mappings
    biblio_mappings = koha_omekas_mapping["biblio"]
    payload = {}
    for mapping in biblio_mapping:
        field = mapping["field"]
        subfield=mapping["subfield"]
        mapping_payload = koha_field_to_payload(record,field, subfield, mapping)
        # need to transform codes and URI!
        # ...

        if mapping["property"] not in payload.keys():
            # create a new one
            payload[mapping["property"]] = mapping_payload
        else:
            # append to existing list
            for statement in mapping_payload:
                payload[mapping["property"]].append(statement)

    return payload


def ingest_biblioitem_payload(payload: dict, template_id: int, new_item: bool):
    """
    Given a template_id, this function ingests biblioitem information on a new item in Omeka S.
    """
    pass

def append_media_to_biblio_item(item_id: int, resource_type: str, koha_omekas_mapping: dict , media_paths):
    """
    Given an Omeka S item ID it returns a payload of files from a media folder (local, to be run from server).
    """
    pass
