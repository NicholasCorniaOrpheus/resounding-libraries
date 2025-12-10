"""Main script for import Allegro catalogue in Koha"""

import sys

sys.path.append("./modules")

from modules.utilities import *
from modules.allegro import *

# Filepaths
adt_filepath = os.path.join("data", "adt")

allegro_koha_mapping = csv2dict(
    os.path.join("data", "mappings", "allegro_koha_mapping.csv")
)


### TO_DO

"""
- Apply Koha mapping to generate new records from  allegro_dictionary using pyMARC
- Test problematic characters to a wider variety of instances, like ò...

"""

#### TEST

read_adt_file(get_latest_file(adt_filepath), allegro_koha_mapping)

#### CODE
