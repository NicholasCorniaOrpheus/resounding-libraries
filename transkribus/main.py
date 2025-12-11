"""Main script for Transkribus import to Koha """

import sys

sys.path.append("./modules")

from modules.utilities import *
from modules.transkribus import *

page_xml_data_directory = os.path.join("data", "page_xml")

json_data_directory = os.path.join("data", "json")

indices_tk_training_id = 257292

# get_transkribus_collections()

# TEST succesfull and ready for production

pages_metadata = get_transkribus_pages_list(257292, 1702668)

get_page_xml(pages_metadata, page_xml_data_directory, json_data_directory)

#### TO-DO:

"""

- Export json data to unique csv {library_identifier,keyword,pages} according to relations and separator for multiple lines
- Map keywords to existing authorities in Koha (get Ton Koopman Keywords from report)
- Record keywords and related pages via the 653 field in Koha via API (retrieve barcode or identifier-> get biblio_id and items)


"""
