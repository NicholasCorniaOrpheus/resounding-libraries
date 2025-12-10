import sys

sys.path.append("./modules")

from modules.utilities import *

problematic_characters_mapping = csv2dict(
    os.path.join("data", "mappings", "problematic_characters.csv")
)


def convert_problematic_characters(string):
    # check if there are problematic characters identified by double \

    separated_string = string.split("\\")
    if len(separated_string) > 1:
        for i in range(len(separated_string)):
            if separated_string[i][0] == "x":
                character_query = list(
                    filter(
                        lambda x: x["value"] == separated_string[i][0:3],
                        problematic_characters_mapping,
                    )
                )

                if len(character_query) > 0:
                    separated_string[i] = separated_string[i].replace(
                        character_query[0]["value"], character_query[0]["replace"]
                    )

        return "".join(separated_string)
    else:
        return string


def read_adt_file(adt_filepath, allegro_koha_mapping, new_record_code="#00"):
    print(f"Opening ADT file... {adt_filepath}")
    # encoding latin-1 because the file is not UTF-* compatible.
    adt_file = open(adt_filepath, "rb")

    decoded_adt = adt_file.read().decode("ascii", errors="backslashreplace")

    # get all lines as list
    # lines = decoded_adt.readlines()
    lines = decoded_adt.split("\n")

    # remove \n and other trims
    for i in range(len(lines)):
        lines[i] = lines[i].strip()

    # create dictionary of records

    allegro_records = []

    for line in lines:
        try:
            # print(f"Current line: {line}")
            if line[0:3] == new_record_code:  # create new record
                # print("Adding new record")
                try:
                    print(f"Record added: {allegro_records[-1]}")

                except IndexError:
                    pass
                allegro_records.append({})
            elif line[0] == "#":  # new field
                # print("Adding field:")
                incipit = line[0:4].strip()
                field = line[4:]
                latin1_field = field.encode("latin-1")
                field = latin1_field.decode("latin-1")
                # print(f"Incipit: {incipit}")
                # print(f"Field: {field}")
                mapping_query = list(
                    filter(lambda x: x["allegro"] == incipit[1:], allegro_koha_mapping)
                )[0]
                if mapping_query["control_field"] != "":
                    allegro_records[-1][mapping_query["allegro"]] = {
                        "koha": mapping_query["koha"],
                        "value": convert_problematic_characters(field),
                    }
                else:
                    allegro_records[-1][mapping_query["allegro"]] = {
                        "koha": mapping_query["koha"],
                        "value": convert_problematic_characters(field),
                        "control_field": mapping_query["control_field"],
                        "control_value": mapping_query["control_value"],
                    }
            else:
                pass
        except IndexError:
            pass
