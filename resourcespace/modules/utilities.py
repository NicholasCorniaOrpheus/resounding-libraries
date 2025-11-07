"""
Utilities functions
"""
"""
Basic utilities scripts
"""
import json, csv, os
from time import gmtime, strftime


def csv2dict(csv_filename):  # imports a CSV file as dictionary
    f = open(csv_filename, "r")
    reader = csv.DictReader(f)
    d = {"items": []}
    for row in reader:
        d["items"].append(row)
    return d["items"]


def json2dict(json_filename):  # imports a JSON file as dictionary
    with open(json_filename, "r") as f:
        json_file = json.load(f)
        return json_file


def dict2json(d, json_filename):  # export a dictionary to JSON file
    json_file = open(json_filename, "w")
    json.dump(d, json_file, indent=2)


def get_current_date():
    return strftime("%Y-%m-%d", gmtime())


def get_latest_file(basepath):  # returns latest file path in a directory
    files = os.listdir(basepath)
    paths = [os.path.join(basepath, basename) for basename in files]
    return max(paths, key=os.path.getctime)


def revert_personal_names_with_comma(string):
    personal_name = string.split(",")
    if len(personal_name) == 1:
        return string
    elif len(personal_name) == 2:  # surname, name format
        name = personal_name[1]
        surname = personal_name[0]
        try:
            if name[0] == " ":
                name = name[1:]
        except IndexError:
            pass
        return f"{name} {surname}"
    else:
        return "Entry with multiple comma: ERROR!"
