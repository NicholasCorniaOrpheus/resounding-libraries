import os, shutil
from zipfile import ZipFile
import zipfile
from time import time
from pathlib import Path


def folder_zip_compression(
    local_dir, compression_level=9
):  # Compress all subfolders in a given directory
    print(local_dir)
    for d in os.listdir(local_dir):
        print(f"Compressing {d} folder...")
        start_time = time()
        with ZipFile(
            os.path.join(local_dir, d + ".zip"),
            "w",
            zipfile.ZIP_DEFLATED,
            compresslevel=compression_level,
        ) as zip_file:
            # recursive file saving using Path.rglob
            src_dir = Path(os.path.join(local_dir, d)).resolve()
            for file in src_dir.rglob("*"):
                # print(file)
                # input()
                if file.is_file():
                    zip_file.write(file, arcname=file.relative_to(src_dir))

        zip_file.close()
        """print("Removing original directory...")
        shutil.rmtree(os.path.join(local_dir, d))
        """
        print(f"Folder compressed in {time() - start_time} seconds.")


print(
    "Provide the absolute directory path for batch compression, such as /volume1/OI_Media/Library/..."
)

condition = False
while condition is not True:
    local_dir = input()
    if os.path.exists(local_dir):
        condition = True
    else:
        print("Incorrect path, retry:")

folder_zip_compression(local_dir)
