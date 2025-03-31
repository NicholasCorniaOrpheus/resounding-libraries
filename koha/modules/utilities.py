"""
Basic utilities scripts
"""
import json, csv
from time import gmtime, strftime
import os
from pymarc import MARCReader, Record, Field, Subfield


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
    json.dump(d, json_file, indent=2, ensure_ascii=False)


def print_mrc_file(filename):  # MARC2TXT operations and split
    f = open(filename, "rb")
    reader = MARCReader(f)
    # Take out the file extension
    out = open(filename[:-4] + ".txt", "w+")
    for record in reader:
        out.write(str(record) + "\n")

    f.close()
    out.close()


def get_current_date():
    return strftime("%Y-%m-%d", gmtime())


def get_latest_file(basepath):  # returns latest file path in a directory
    files = os.listdir(basepath)
    paths = [os.path.join(basepath, basename) for basename in files]
    return max(paths, key=os.path.getctime)
