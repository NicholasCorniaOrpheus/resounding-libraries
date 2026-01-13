""" 
This scripts tries to automaticcaly match a "keyword" and "pages-keyword" labelled region
with a relation according to their centroids position (horizontal alignment)


Syntax for relation in PAGE XML

<Relations>
    <Relation type="link" custom="relationName {value:related_pages;}">
        <RegionRef regionRef="r_5"/>
        <RegionRef regionRef="r_10"/>
    </Relation>

"""

import sys

sys.path.append("./modules")

from modules.utilities import *

import xml.etree.ElementTree as ET


def get_polygonal_centroids(
    coordinate_list,
):  # Returns the centroids of a lsit of coordinates [(x_1,y_1), ... (x_n,x_n)]
    n = len(coordinate_list)
    sum_x = float(0)
    sum_y = float(0)
    for point in coordinate_list:
        sum_x += point[0]
        sum_y += point[1]

    return (sum_x / n, sum_y / n)


def find_region_polygonal_coordinates(
    region_id, root
):  # Returns a list of coordinates given the region id, for example r_1
    coordinates = []
    for region in root.findall(
        "./{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}Page/{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}TextRegion"
    ):
        if region.attrib["id"] == region_id:
            coordinates_element = region.find(
                "./{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}Coords"
            )
            points_string = coordinates_element.attrib["points"]
            points_list = points_string.split(" ")
            for point in points_list:
                x = int(point.split(",")[0])
                y = int(point.split(",")[1])
                coordinates.append((x, y))

            return coordinates


def get_region_coordinates(
    region,
):  # Returns a list of coordinates given an etree region element.
    coordinates = []
    coordinates_element = region.find(
        "./{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}Coords"
    )
    points_string = coordinates_element.attrib["points"]
    points_list = points_string.split(" ")
    for point in points_list:
        x = int(point.split(",")[0])
        y = int(point.split(",")[1])
        coordinates.append((x, y))

    return coordinates
