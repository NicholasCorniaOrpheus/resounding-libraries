# Omeka S Tools

import sys

sys.path.append("./modules")  # importing custom functions in modules
from modules.utilities import *

from omeka_s_tools.api import OmekaAPIClient
import requests
from copy import deepcopy
import json


# Import credentials, assuming you are running the code from the `koha` directory
credentials = json2dict("../credentials/credentials.json")

omekas_credentials = {
    "api_url": credentials["omekas"]["api_url"],
    "key_identity": credentials["omekas"]["key_identity"],
    "key_credential": credentials["omekas"]["key_credential"],
}


# Initialize Client
omekas_session = OmekaAPIClient(
    api_url=omekas_credentials["api_url"],
    key_identity=omekas_credentials["key_identity"],
    key_credential=omekas_credentials["key_credential"],
)


def change_item_property_value(value: str, property_name: str,resource_id: int, resource_type: str, session=omekas_session, value_position=0) -> dict:
    """Change the value of a specific statement of a property of a given resource.
    Args:
                value (str): new value for the property.
                property_name (str): name of the property to be updated
                resource_id (int): ID of the item set to be added to the site.
                site_id (int): ID of the site to which the item set will be added.
                session (oauth2): Oauth 2 session for Omeka S.
                value_position (int): position of the value to be change, in case of multiple statements for property. 0 is default.

    Returns:
                response (dict): JSON response from API.

    """
    data = session.get_resource_by_id(resource_id, resource_type=resource_type)
    data[property_name][value_position]["@value"] = value
    session.update_resource(data, resource_type=resource_type)




# Not working, giving 500 HTTP error. Apparently, Item Sets have no `o:site` property!!!!
def add_item_set_to_site(resource_id: int, site_id: int,session=omekas_session) -> dict:
    """
    Args:
                resource_id (int): ID of the item set to be added to the site.
                site_id (int): ID of the site to which the item set will be added.
                session (oauth2): Oauth 2 session for Omeka S.

    Returns:
                response (dict): JSON response from API.

    """
    # Get resource first
    data = session.get_resource_by_id(resource_id, resource_type="item_sets")
    # add site to resource
    if "o:site" not in data.keys():
        data["o:site"] = [{"@id": f"{omekas_credentials["api_url"]}/sites/{str(site_id)}", "o:id": site_id}]
    else:
        if not any(site["o:id"] == site_id for site in data["o:site"]):
            data["o:site"].append({"@id": f"{omekas_credentials["api_url"]}/sites/{str(site_id)}", "o:id": site_id})

    print(f"Modified data: {data}")

    # update resource back to Omeka S via API
    response = session.update_resource(data, resource_type="item_sets")

    print(response)


