"""
This script is going to bulk download TIF files from an ftp server
and compress them as zip
"""

import paramiko
import json
import os, shutil
from datetime import datetime
from zipfile import ZipFile
import zipfile


def json2dict(json_filename):  # imports a JSON file as dictionary
    with open(json_filename, "r") as f:
        json_file = json.load(f)
        return json_file


def sftp_session(hostname, port, username, password):
    # Create a SSH client
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Connect to the SFTP server
    ssh_client.connect(hostname, port, username, password)

    # Create SFTP session

    return ssh_client.open_sftp()


def sftp_download_tiff_dir(sftp, d, tiff_dir, local_dir):
    # I am assuming no nested subdirectories.

    # Check duplicates
    if d in os.listdir(local_dir):
        print(f"Folder {d} already present. Skip...")
    else:
        print(f"Downloading {d} folder...")
        os.mkdir(os.path.join(local_dir, d))
        for file in sftp.listdir(os.path.join(tiff_dir, d)):
            sftp.get(os.path.join(tiff_dir, d, file), os.path.join(local_dir, d, file))


def tif_zip_compression(local_dir, d):  # Compress all TIFF files in given directory
    print(f"Compressing {d} folder...")
    with ZipFile(d + ".zip", "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file in os.listdir(os.path.join(local_dir, d)):
            zip_file.write(os.path.join(local_dir, d, file))

    zip_file.close()
    # remove TIFF files
    print("Removing original TIFF files...")
    for file in os.listdir(os.path.join(local_dir, d)):
        os.remove(os.path.join(local_dir, d, file))
    # move zip file back to directory
    shutil.move(d + ".zip", os.path.join(local_dir, d))


# import credentials
credentials = json2dict("../credentials/credentials.json")

hostname = credentials["sftp"]["hostname"]
port = 22
username = credentials["sftp"]["username"]
password = credentials["sftp"]["password"]
tiff_dir = credentials["sftp"]["tiff_dir"]

# Create SFTP session
sftp = sftp_session(hostname, port, username, password)

# Get list of TIFF directories
tiff_list = sftp.listdir(tiff_dir)

# Local directory list
local_dir = "/volume1/OI_Media/Library/iGuana_2025/DATA/TIFF"

for d in os.listdir(local_dir):
	if len(os.listdir(os.path.join(local_dir,d))) > 1:
		tif_zip_compression(local_dir, d)
