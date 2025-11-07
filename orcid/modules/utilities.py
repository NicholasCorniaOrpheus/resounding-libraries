import json, csv
import pandas as pd
from time import gmtime, strftime
import os


def csv2dict(csv_filename):  # imports a CSV file as dictionary
    f = open(csv_filename, "r")
    reader = csv.DictReader(f)
    d = {"items": []}
    for row in reader:
        d["items"].append(row)
    return d["items"]


def dict2csv(d, csv_filename):
    df = pd.DataFrame(data=d)
    df.to_csv(csv_filename, sep=",", index=False)


def json2dict(json_filename):  # imports a JSON file as dictionary
    with open(json_filename, "r") as f:
        json_file = json.load(f)
        return json_file


def dict2json(d, json_filename):  # export a dictionary to JSON file
    json_file = open(json_filename, "w")
    json.dump(d, json_file, indent=2, ensure_ascii=False)
