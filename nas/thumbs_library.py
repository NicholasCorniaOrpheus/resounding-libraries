import os, shutil
import pyvips
from glob import glob
from pathlib import Path
from multiprocessing import Pool

from time import datetime


def thumbnail_conversion_file(f,out_dir, width=width,height=height):

	out = pyvips.Image.thumbnail(f,width=width,height=height)

	out_name = f.replace("_001.jpg",".gif")
    img.write_to_file(os.path.join(out_dir,out_name.split("/")[-1]))
    

#### CODE #####

working_dir = input("Provide the (absolute) directory path for batch conversion, such as /volume1/OI_Media/Library/... \n")

width, height = input("Provide the width and height for the thumbnails, such as 200 300 \n").split(" ")

out_dir = input("Provide output directory path for thumbs such as ./thumbs")

if os.path.exists(out_dir):
		pass
else:
	os.mkdir(out_dir)
	print("Directory path was not defined, created it. ")




# Converting images using multiprocessing

if __name__ == "__main__":
	start_time = datetime.datetime.now()
    number_directories = len(os.listdir(working_dir))
    processed = 0
    for d in os.listdir(working_dir):
        print(f"Getting thumbs from {d} directory...")
        current_directory = os.path.join(working_dir, d)
        files = glob(current_directory + "/*.jpg")
        files_to_be_converted = []
        # convert first page
        first_page_query = list(filter(lambda x: x.endswith("001.jpg"), files))
        if len(first_page_query) > 0:
        	files_to_be_converted.append(first_page_query[0])

        
        with Pool(10) as pool:
            pool.map(thumbnail_conversion_file, files_to_be_converted)

        processed += 1
        print(f"Process completed: {100*float(processed)/number_directories}%")

    end_time = datetime.datetime.now()
    diff = end_time - start_time
    print(f"Time taken: {diff.seconds} s")
    