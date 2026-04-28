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

adt_filename = "kast48-Bussem-20251217.adt"

allegro_records = read_adt_file(
    os.path.join(adt_filepath, adt_filename), allegro_koha_mapping
)

print(f"Saving {adt_filename} as JSON... ")

dict2json(
    allegro_records, os.path.join("data", "json", adt_filename.replace(".adt", ".json"))
)


#### CODE
