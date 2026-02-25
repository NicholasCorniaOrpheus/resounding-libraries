import os, shutil
from zipfile import ZipFile
import zipfile
from time import time


def tif_zip_compression(local_dir, d):  # Compress all TIFF files in given directory
    dir_list = [
        file.name.endswith(".zip") for file in os.scandir(os.path.join(local_dir, d))
    ]
    if True not in dir_list:
        print(f"Compressing {d} folder...")
        start_time = time()
        with ZipFile(d + ".zip", "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file in os.scandir(os.path.join(local_dir, d)):
                if file.name.endswith(".tif"):
                    zip_file.write(file.path, arcname=file.name)

        zip_file.close()
        # remove TIFF files
        print("Removing original TIF files...")
        for file in os.scandir(os.path.join(local_dir, d)):
            if file.name.endswith(".tif"):
                os.remove(file.path)
        # move zip file back to directory
        shutil.move(d + ".zip", os.path.join(local_dir, d))
        print(f"Folder compressed in {time() - start_time} seconds.")
    else:
        print(f"Folder {d} already compressed. Skipping...")


print(
    "Provide the absolute directory path for the batch TIF compression, such as /volume1/OI_Media/Library/..."
)

condition = False
while condition is not True:
    local_dir = input()
    if os.path.exists(local_dir):
        condition = True
    else:
        print("Incorrect path, retry:")

# Applying compression to all subfolders

for d in os.scandir(local_dir):
    if os.path.isdir(d.path):
        tif_zip_compression(local_dir, d.name)
