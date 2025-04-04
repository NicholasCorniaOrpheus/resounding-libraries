"""
Basic utilities scripts
"""
import json, csv
import pandas as pd
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


# Given a URL, from the MARC 856$u field, returns the source authority for subfield 856$3
def get_external_source_authority(url, external_source_list):
    for source in external_source_list:
        print(source)
        for base_url in source["base_url"]:
            if base_url in url:
                return source["label"]

    return ""


def get_abbreviation_code_data(code, abbreviation_list):
    query = list(filter(lambda x: x["code"] == code, abbreviation_list))
    if len(query) > 0:
        # return the found abbreviation, assuming unique codes
        return query[0]
    else:
        return {"code": code, "label": "", "wd_label": "", "wd_qid": ""}
