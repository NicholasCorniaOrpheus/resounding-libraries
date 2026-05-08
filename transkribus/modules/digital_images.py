"""
Scripts for importing and working with digital scans.

1. transform pdfs from special collections into jpgs, by renaming the shelfmark into barcode.
2. 

"""
import sys

sys.path.append("./modules")

from modules.utilities import *
from modules.koha import *

import pathlib
import os
import csv
import pdf2image


# def shelfmark_to_barcode(shelfmark: str, shelfmark_barcode_mapping: list) -> str:
#     """
#     Given a shelfmark, returns the unique barcode associated to it, based on a mapping.
#     """
#     query_shelfmark = list(
#         filter(lambda x: x["shelfmark"] == shelfmark, shelfmark_barcode_mapping)
#     )

#     if len(query_shelfmark) == 1:
#         # one unique solution
#         barcode = query_shelfmark[0]["barcode"]
#         return barcode
#     elif len(query_shelfmark) > 1:
#         # multiple results
#         print(
#             f"The shelfmark {shelfmark} is associated with multiple barcodes: {query_shelfmark}"
#         )
#         input()
#     else:
#         print(f"Shelfmark {shelfmark} not found.")


def convert_pdfs_to_images(
    directories_path: str,
    output_path: str,
    call_number_barcode_filepath: str,
    convert_shelfmark_to_barcode=True,
):
    """
    Converts a series of PDFs, stored in an arbitrary tree of directories into a series of directories with JPG images.

    Args:
    directories_path (str): parent directory where the PDFs are stored.
    output_path (str): output parent directory for conversion.
    convert_shelfmark_to_barcode (bool): Rename shelfmark in PDF filename to barcode. Default is `True`.

    """
    # get all pdfs in the directory tree
    pdf_files = []
    for f in pathlib.Path(directories_path).rglob("*.pdf"):
        pdf_files.append(f)

    # get call_number-shelfmark mapping
    f = open(call_number_barcode_filepath, "r", encoding="utf-8")
    reader = csv.DictReader(
        f, delimiter=";", fieldnames=["biblionumber", "barcode", "call_number"]
    )
    d = {"items": []}
    for row in reader:
        d["items"].append(row)
    call_number_barcode = d["items"]
    # extract shelfmark from call_number
    for item in call_number_barcode:
        item["shelfmark"] = item["call_number"].split(" ")[-1]

    # extract shelfmark from pdf files
    missing_match = []
    for pdf in pdf_files:
        shelfmark_pdf = pdf.stem.split(" ")[0]
        query_shelfmark = list(
            filter(lambda x: x["shelfmark"] == shelfmark_pdf, call_number_barcode)
        )
        if len(query_shelfmark) == 1:
            barcode = query_shelfmark[0]["barcode"]
            # extract images from pdf path
            images = pdf2image.convert_from_path(pdf)
            # set up output directory
            if os.path.exists(os.path.join(output_path, barcode)):
                pass
            else:
                os.makedirs(os.path.join(output_path, barcode))
            output_dir = os.path.join(output_path, barcode)
            for i in range(len(images)):
                page = str(i + 1)
                images[i].save(
                    os.path.join(output_dir, f"{barcode}_{page.zfill(3)}.jpg"), "JPEG"
                )

            print(f"PDF file {pdf.stem} has been exported!")
        else:
            # append to missing match
            missing_match.append(pdf)
            print(f"Missing: {pdf}")

    print(f"Missing PDFs for matching are {len(missing_match)} \n  {missing_match}")
