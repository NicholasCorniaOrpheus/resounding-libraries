""" Series of scripts in order to interact witht he Omeka S API and generate specific things"""

import sys

sys.path.append("./modules")  # importing custom functions in modules
from modules.utilities import *
from modules.rdf import *
from modules.api import *


#### TEST #####

# get allo items
data = omekas.get_resources("items")

# get a specific item by id
omeka_id = 1
data = omekas.get_resource_by_id(omeka_id, resource_type="items")

# get resource by term and vocabukar

# STILL NOT WORKING PROPERLY...
