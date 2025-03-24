'''
Resource Space API actions
'''

import requests

rsQueries = {
    "add_resource_to_collection": {
        "queryParameters": ["resource", "collection"],
        "rsDocumentationUrl": "https://www.resourcespace.com/knowledge-base/api/add_resource_to_collection",
    },
    "collection_remove_resources":{
        "queryParameters": ["collection", "resources", "removeall", "selected"],
        "rsDocumentationUrl": "https://www.resourcespace.com/knowledge-base/api/collection_remove_resources",
    },
    "create_collection":{
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
    "get_resource_data":{
        "queryParameters": ["resource"],
        "queryReturn": "JSON of all metadata concerning the collection",
        "rsDocumentationUrl": "https://www.resourcespace.com/knowledge-base/api/get_resource_data",
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
    "save_collecton": {
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
        "queryName": ,
        "queryParameters": ["ref", "no_exif", "revert", "autorotate", "file_path"],
        "queryReturn": "Uploads a new local file to an existing resource, replacing any file that is already attached.",
        "rsDocumentationUrl": "https://www.resourcespace.com/knowledge-base/api/upload_file",
    },
}  # List of Resource Space API possible queries


def rsQueriesIndex(name, rsQueries):
    # Return the index given a queryName
    for i in range(len(rsQueries)):
        query = rsQueries[i]
        if query["queryName"] == name:
            print(i)
            return i
    return "error!!!"


def sha2hexa(string):
    string = string.encode("utf-8")
    sha256 = hashlib.sha256()
    sha256.update(string)
    return sha256.hexdigest()


def apiQuery(credentials, query, parameters):
    queryParameters = ""
    for i in range(len(query["queryParameters"])):
        queryParameters += "&" + query["queryParameters"][i] + "=" + parameters[i]

    query = (
        "user="
        + credentials["user"]
        + "&function="
        + query["queryName"]
        + queryParameters
    )
    print("Query before:", query)
    # query = query.replace(":", "%3A")  # turn : in ASCII
    # query = query.replace(",", "%2C")  # turn comma into ASCII
    # query = query.replace(" ", "+")  # turn ASCII space into +
    sign = "&sign=" + sha2hexa(credentials["privateKey"] + query)
    print("Signature:", sign, "\n")
    print("Query: ", query, "\n")
    # setting headers for security issues
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }
    response = requests.get(
        credentials["rsApiUrl"] + "?" + query + sign, headers=headers
    )
    print(response.status_code)
    return response