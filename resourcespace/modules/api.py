"""
Resource Space API actions
"""

import requests
import subprocess
import hashlib

rsQueries = {
    "add_resource_to_collection": {
        "queryParameters": ["resource", "collection"],
        "rsDocumentationUrl": "https://www.resourcespace.com/knowledge-base/api/add_resource_to_collection",
    },
    "collection_remove_resources": {
        "queryParameters": ["collection", "resources", "removeall", "selected"],
        "rsDocumentationUrl": "https://www.resourcespace.com/knowledge-base/api/collection_remove_resources",
    },
    "create_collection": {
        "queryParameters": ["name"],
        "queryReturn": "new_collection_id",
        "rsDocumentationUrl": "https://www.resourcespace.com/knowledge-base/api/create_collection",
    },
    "create_resource": {
        "queryParameters": ["resource_type"],
        "queryReturn": "new_resource_id",
        "rsDocumentationUrl": "https://www.resourcespace.com/knowledge-base/api/create_collection",
    },
    "get_collection": {
        "queryParameters": ["ref"],
        "queryReturn": "JSON_collection",
        "rsDocumentationUrl": "https://www.resourcespace.com/knowledge-base/api/get_collection",
    },
    "delete_collection": {
        "queryParameters": ["ref"],
        "queryReturn": "JSON_collection",
        "rsDocumentationUrl": "https://www.resourcespace.com/knowledge-base/api/get_collection",
    },
    "get_data_by_field": {
        "queryParameters": ["ref", "field"],
        "queryReturn": "Returns field value from field ID or shortname",
        "rsDocumentationUrl": "https://www.resourcespace.com/knowledge-base/developers/functions/get_data_by_field",
    },
    "get_featured_collections": {
        "queryParameters": ["parent"],
        "queryReturn": "What is the parent?",
        "rsDocumentationUrl": "https://www.resourcespace.com/knowledge-base/api/get_featured_collections",
    },
    "get_resource_collections": {
        "queryParameters": ["ref"],
        "queryReturn": "JSON of Collections including the given resource, with collection id (ref) and name.",
        "rsDocumentationUrl": "https://www.resourcespace.com/knowledge-base/api/get_resource_collections",
    },
    "get_resource_data": {
        "queryParameters": ["resource"],
        "queryReturn": "JSON of all metadata concerning the collection",
        "rsDocumentationUrl": "https://www.resourcespace.com/knowledge-base/api/get_resource_data",
    },
    "get_resource_path": {
        "queryParameters": ["ref"],
        "queryReturn": "URL of resource image",
        "rsDocumentationUrl": "https://www.resourcespace.com/knowledge-base/api/get_resource_path",
    },
    "get_user_collections": {
        "queryParameters": [],
        "queryReturn": "JSON of all collection owned by the current user, thus the one in the credentials!",
        "rsDocumentationUrl": "https://www.resourcespace.com/knowledge-base/api/get_user_collections",
    },
    "update_field": {
        "queryParameters": ["resource", "field", "value"],
        "queryReturn": "true if correct stated, false otherwise",
        "rsDocumentationUrl": "https://www.resourcespace.com/knowledge-base/api/get_user_collections",
    },
    "save_collection": {
        "queryParameters": ["ref", "coldata"],
        "queryReturn": "You can modify several collection data, such as type=4 for public collection, parent=ID of parent directory...",
        "rsDocumentationUrl": "https://www.resourcespace.com/knowledge-base/api/save_collection",
    },
    "search_public_collections": {
        "queryParameters": ["search", "exclude_themes"],
        "queryReturn": "Given a searchString return a list of collections. Set exclude themes to false",
        "rsDocumentationUrl": "https://www.resourcespace.com/knowledge-base/api/search_public_collections",
    },
    "upload_file": {
        "queryParameters": ["ref", "no_exif", "revert", "autorotate", "file_path"],
        "queryReturn": "Uploads a new local file to an existing resource, replacing any file that is already attached.",
        "rsDocumentationUrl": "https://www.resourcespace.com/knowledge-base/api/upload_file",
    },
}  # List of Resource Space API possible queries


# IT WORKS!!!!
def rs_API_cURL_POST(rs_credentials, query_name, parameters):
    # cURL = """private_key="4864ade3f2286db4ae7b17076a1608ca710b4d67709be962edf6fb83b84a2597";user='nicholas.cornia';query='user=nicholas.cornia&function=get_resource_path&ref=10';sign=$(echo -n "${private_key}${query}" | openssl dgst -sha256);curl -X POST "http://192.168.0.5/resourcespace/api/?${query}&sign=$(echo ${sign} | sed 's/^.* //')" """
    queryParameters = ""
    for i in range(len(rsQueries[query_name]["queryParameters"])):
        queryParameters += (
            "&" + rsQueries[query_name]["queryParameters"][i] + "=" + parameters[i]
        )

    query = (
        "user="
        + rs_credentials["username"]
        + "&function="
        + query_name
        + queryParameters
    )
    query = query.replace("{", "%7B")
    query = query.replace(" ", "+")
    query = query.replace("}", "%7D")
    query = query.replace('"', "%22")
    query = query.replace(":", "%3A")

    sign = "&sign=" + sha2hexa(rs_credentials["secret_key"] + query)
    cURL = f"""curl -X POST "{rs_credentials["rs_api_url"]}{query}{sign}" """
    p = subprocess.run(
        cURL, shell=True, check=True, capture_output=True, encoding="utf-8"
    )
    #print(p.args)
   return p.stdout

def sha2hexa(string):
    string = string.encode("utf-8")
    sha256 = hashlib.sha256()
    sha256.update(string)
    return sha256.hexdigest()


def rs_API_requests_GET(credentials, query_name, parameters):
    queryParameters = ""
    for i in range(len(rsQueries[query_name]["queryParameters"])):
        queryParameters += "&" + rsQueries[query_name]["queryParameters"][i] + "=" + parameters[i]

    query = (
        "user="
        + credentials["user"]
        + "&function="
        + query["queryName"]
        + queryParameters
    )
    query = query.replace("{", "%7B")
    query = query.replace(" ", "+")
    query = query.replace("}", "%7D")
    query = query.replace('"', "%22")
    query = query.replace(":", "%3A")
    sign = "&sign=" + sha2hexa(credentials["private_key"] + query)
    # setting headers for security issues
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }
    response = requests.get(
        credentials["rs_api_url"] + "?" + query + sign, headers=headers
    )
    print(response.status_code)
    return response
