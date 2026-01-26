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

# Libraries for clustering algorithm visualization process
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt
import urllib.request

sys.path.append("./modules")

from modules.utilities import *
from modules.transkribus import *

import xml.etree.ElementTree as ET

import statistics
import math
from scipy import stats  # trimmed_mean


def show_cluster_algorithm_process(page_metadata):
    # Get JPG image
    ### TO BE CONTINUED... not easy to integrate it in the existent spotting function.
    image_filepath = get_jpg_from_transkribus(page_metadata)

    pass


def get_polygonal_centroids(
    coordinate_list,
):  # Returns the centroids of a lsit of coordinates [(x_1,y_1), ... (x_n,x_n)]
    n = len(coordinate_list)
    if n > 0:
        sum_x = float(0)
        sum_y = float(0)
        for point in coordinate_list:
            sum_x += point[0]
            sum_y += point[1]

        return (sum_x / n, sum_y / n)
    else:
        return (0, 0)


def get_trim_mean_polygonal_length(
    regions, trim_cut=0.1
):  # This script provides a heuristic threshold for the vertical_clustering_relations_matching algorithm
    lengths = []
    for region in regions:
        # Get maximal x distance between points of coordinates
        max_x = float(0)
        min_x = float(0)
        for point in region["coordinates"]:
            if point[0] > max_x:
                max_x = point[0]
            if point[0] < min_x:
                min_x = point[0]

        lengths.append(max_x - min_x)

    trimmed_mean = stats.trim_mean(lengths, trim_cut)

    # print(lengths)
    # print(f"Trimmed mean: {trimmed_mean}")
    # input()

    return trimmed_mean


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


def get_regions_from_xml(root, baseline=True):
    regions = []

    # Get data from each region, including centroids and coordinates
    for text_region in root.findall(
        "./{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}Page/{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}TextRegion"
    ):
        if baseline == True:
            coordinates = get_region_coordinates_from_baselines(text_region)
        else:  # getting coordinates from regional polygon
            coordinates = get_region_coordinates(text_region)
        try:
            region_type = text_region.attrib["custom"].split("type:")[1].split(";")[0]
        except IndexError:  # in case no type is defined.
            region_type = ""
        regions.append(
            {
                "region_id": text_region.attrib["id"],
                "type": region_type,
                "text": [],
                "coordinates": coordinates,
                "centroids": get_polygonal_centroids(coordinates),
            }
        )
        # Get text lines
        xml_textlines = text_region.findall(
            "./{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}TextLine"
        )
        for xml_line in xml_textlines:
            regions[-1]["text"].append(
                xml_line.find(
                    "./{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}TextEquiv/{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}Unicode"
                ).text
            )

    return regions


def get_region_coordinates_from_baselines(
    region,
    text_line_schema="./{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}TextLine",
    baseline_schema="./{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}Baseline",
):  # Returns a list of coordinates based on baselines given an etree region element.
    coordinates = []
    textline_elements = region.findall(text_line_schema)
    points_string = ""
    for textline in textline_elements:
        baseline_element = textline.find(baseline_schema)
        points_string += baseline_element.attrib["points"] + " "

    points_list = points_string.split(" ")[:-1]
    for point in points_list:
        x = int(point.split(",")[0])
        y = int(point.split(",")[1])
        coordinates.append((x, y))

    return coordinates


def get_region_coordinates(
    region,
    coordinate_schema="./{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}Coords",
):  # Returns a list of coordinates given an etree region element.
    coordinates = []
    coordinates_element = region.find(coordinate_schema)
    try:
        points_string = coordinates_element.attrib["points"]
    except AttributeError:
        print(coordinates_element)
        input()
    points_list = points_string.split(" ")
    for point in points_list:
        x = int(point.split(",")[0])
        y = int(point.split(",")[1])
        coordinates.append((x, y))

    return coordinates


def ingest_relations_to_xml(relations, root):
    # Parse new automatic relations back to PAGE XML. This script will not overwrite existing relations

    page_xml = root.find(
        "./{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}Page"
    )

    relations_xml = root.find(
        "./{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}Page/{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}Relations"
    )
    if relations_xml == None:  # Relations is empty
        relations_xml = ET.SubElement(
            page_xml,
            "{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}Relations",
        )
        # page_xml.append(relations_xml)
    else:
        # Cleaning up previous relations!
        for relation in relations_xml:
            relations_xml.remove(relation)


    for relation in relations:
        # Create a new element for each relation
        relation_element = ET.Element("Relation")
        # Set attribute type to link and custom according to Transkribus notation
        relation_element.set("type", "link")
        relation_element.set("custom", f"relationName {{value:{relation['type']};}}")
        # Generate subelement RegionRef for source and target
        source_region_ref = ET.Element("RegionRef")
        source_region_ref.set("regionRef", relation["source"])
        target_region_ref = ET.Element("RegionRef")
        target_region_ref.set("regionRef", relation["target"])
        relation_element.append(source_region_ref)
        relation_element.append(target_region_ref)
        relations_xml.append(relation_element)

    return root


def simple_relations_matching(
    regions,
    source_region_type="keyword",
    target_region_type="pages-keyword",
    relations_type="related_pages",
):
    # Split regions in two ordered list (one for source and one for target) according to centroids y coordinate.
    source_regions = sorted(
        [region for region in regions if region["type"] == source_region_type],
        key=lambda k: k["centroids"][1],
    )
    target_regions = sorted(
        [region for region in regions if region["type"] == target_region_type],
        key=lambda k: k["centroids"][1],
    )

    # print(f"Source regions: {", ".join([region["region_id"] for region in source_regions])}")
    # print(f"Target regions: {", ".join([region["region_id"] for region in target_regions])}")

    # Generate relations to minimal distance criterium between source and target
    relations = []
    for source_region in source_regions:
        # get closest target region
        min_region = None
        for target_region in target_regions:
            if min_region is None:
                min_region = target_region
            else:
                if abs(
                    source_region["centroids"][1] - target_region["centroids"][1]
                ) < abs(source_region["centroids"][1] - min_region["centroids"][1]):
                    min_region = target_region

        relations.append(
            {
                "type": relations_type,
                "source": source_region["region_id"],
                "target": min_region["region_id"],
            }
        )

    return relations



# Older version
def vertical_clustering_relations_matching_v1(
    regions,
    source_region_type="keyword",
    target_region_type="pages-keyword",
    relations_type="related_pages",
    trim_cut=0.3,
):
    # This script recursively builds clusters of regions according to their vertical centroid distance
    clusters = []
    source_regions = [
        region for region in regions if region["type"] == source_region_type
    ]
    # add the single regions into the cluster as one_element
    for source_region in source_regions:
        clusters.append(
            {
                "regions": [source_region],
                "trim_mean_x_centroid": source_region["centroids"][0],
            }
        )

    print(f"Number of source regions: {len(source_regions)}")

    # Get threshold based on the Otsu x-gaps trimmed mean
    threshold = 0
    x_gaps = []
    for source_region in clusters:
        for region in clusters:
            if region != source_region:
                x_gaps.append(
                    abs(
                        source_region["trim_mean_x_centroid"]
                        - region["trim_mean_x_centroid"]
                    )
                )

    threshold = stats.trim_mean(x_gaps, trim_cut)

    print(f"threshold value: {threshold} ")

    # Iterate until the culsters aggregate according to threshold value
    loop_condition = True
    while loop_condition:
        loop_condition = False
        # Get minimal cluster and append the source cluster to it
        for source_cluster in clusters:
            # print(f"Current source cluster: {source_cluster}")
            # input()
            min_cluster = None
            for cluster in clusters:
                # print(f"Current cluster: {cluster}")
                if cluster != source_cluster:
                    if min_cluster is None:
                        min_cluster = cluster
                    else:
                        cluster_distance = abs(
                            source_cluster["trim_mean_x_centroid"]
                            - cluster["trim_mean_x_centroid"]
                        )
                        # print(cluster_distance)
                        if cluster_distance < abs(
                            source_cluster["trim_mean_x_centroid"]
                            - min_cluster["trim_mean_x_centroid"]
                        ):
                            # apply threshold condition, otherwise the algorithm will converge to a single cluster
                            if cluster_distance < threshold:
                                min_cluster = cluster
                                loop_condition = True

            if loop_condition:
                # Append source_cluster to min_cluster and update average centroid
                """print(
                                f"Source cluster: {source_cluster} \n Minimal cluster: {min_cluster}"
                )
                """
                min_cluster["regions"] += source_cluster["regions"]
                # print(f"Updated minimal cluster: {min_cluster}")
                min_cluster["trim_mean_x_centroid"] = float(
                    stats.trim_mean(
                        [region["centroids"][0] for region in min_cluster["regions"]],
                        trim_cut,
                    )
                )
                # remove source_cluster
                clusters.remove(source_cluster)

    print(f"Number of clusters: {len(clusters)}")
    #print(f"Clusters: {clusters}")
    input()

    # Initiate target_regions
    target_regions = [
        region for region in regions if region["type"] == target_region_type
    ]
    relations = []
    # Assign relation to best fitting cluster element, this time based on y-centroid value, taking into account that the target region should be matched to the closest (according to x-centroid) cluster to the LEFT (Western reading order!)
    for target_region in target_regions:
        # determine the best cluster for the target according to x-centroid and reading order left
        min_cluster = None
        for cluster in clusters:
            if cluster["trim_mean_x_centroid"] < target_region["centroids"][0]:
                if min_cluster is None:
                    min_cluster = cluster
                else:
                    if abs(
                        target_region["centroids"][0] - cluster["trim_mean_x_centroid"]
                    ) < abs(
                        target_region["centroids"][0]
                        - min_cluster["trim_mean_x_centroid"]
                    ):
                        min_cluster = cluster

        if min_cluster is None:  # there must be an error with clustering
            print(
                "An error has occurred in the clustering, finding no cluster of sources left from target, we will just use the horizontal position"
            )
            print(f"Problematic target: {target_region}")
            for cluster in clusters:
                if min_cluster is None:
                    min_cluster = cluster
                else:
                    if abs(
                        target_region["centroids"][0] - cluster["trim_mean_x_centroid"]
                    ) < abs(
                        target_region["centroids"][0]
                        - min_cluster["trim_mean_x_centroid"]
                    ):
                        min_cluster = cluster

        # best fit according to y-centroid for the min_cluster
        best_region = None
        for cluster_region in min_cluster["regions"]:
            if best_region is None:
                best_region = cluster_region
            else:
                if abs(
                    target_region["centroids"][1] - cluster_region["centroids"][1]
                ) < abs(target_region["centroids"][1] - best_region["centroids"][1]):
                    best_region = cluster_region

        # append the relation to the relations dictionary
        relations.append(
            {
                "type": relations_type,
                "source": best_region["region_id"],
                "target": target_region["region_id"],
            }
        )

    # Return the regions dictionary
    return relations




# Newer version, with dynamical threshold
def vertical_clustering_relations_matching(
    regions,
    source_region_type="keyword",
    target_region_type="pages-keyword",
    relations_type="related_pages",
    trim_cut=0.35,
):
    # This script recursively builds clusters of regions according to 2D neighboorhood distance
    clusters = []
    # Initiate target and source regions
    source_regions = [
        region for region in regions if region["type"] == source_region_type
    ]

    target_regions = [
        region for region in regions if region["type"] == target_region_type
    ]
    # add the single regions into the cluster as one_element
    for source_region in source_regions:
        clusters.append(
            {
                "regions": [source_region],
                "type": source_region_type,
                "trim_mean_x_centroid": source_region["centroids"][0],
            }
        )
    for target_region in target_regions:
        clusters.append(
            {
                "regions": [target_region],
                "type": target_region_type,
                "trim_mean_x_centroid": target_region["centroids"][0],
            }
        )

    print(f"Number of source and target regions: {len(clusters)}")
 
    # Iterate until the culsters aggregate according to region type
    loop_condition = True
    while loop_condition:
        loop_condition = False
        # Get minimal cluster and append the source cluster to it
        target_clusters = list(filter(lambda x: x["type"] == target_region_type, clusters))
        source_clusters = list(filter(lambda x: x["type"] == source_region_type, clusters))
        for ref_cluster in clusters:
            # print(f"Current source cluster: {source_cluster}")
            # input()
            cluster_type = ref_cluster["type"]
            if cluster_type == source_region_type:
                # Calculate minimal distance between source cluster and target clusters. It will be used as dynamic threshold for the clustering algorithm
                minimal_source_target_distance = min([abs(ref_cluster["trim_mean_x_centroid"] - target_cluster["trim_mean_x_centroid"]) for target_cluster in target_clusters])
            else:
                # Calculate minimal distance between target cluster and source clusters. It will be used as dynamic threshold for the clustering algorithm
                minimal_source_target_distance = min([abs(ref_cluster["trim_mean_x_centroid"] - source_cluster["trim_mean_x_centroid"]) for source_cluster in source_clusters])

            print(f"Dynamic minimal source-target distance: {minimal_source_target_distance}")
            min_cluster = None
            for cluster in clusters:
                # print(f"Current cluster: {cluster}")
                if cluster != ref_cluster:
                    if cluster["type"] == cluster_type:
                        if min_cluster is None:
                            min_cluster = cluster
                        else:
                            cluster_distance = abs(
                                ref_cluster["trim_mean_x_centroid"]
                                - cluster["trim_mean_x_centroid"]
                            )
                            # print(cluster_distance)
                            if cluster_distance < abs(
                                ref_cluster["trim_mean_x_centroid"]
                                - min_cluster["trim_mean_x_centroid"]
                            ):
                                # apply threshold condition based on minimal source-target distance, otherwise the algorithm will converge to a single cluster
                                if cluster_distance < minimal_source_target_distance:
                                    min_cluster = cluster
                                    loop_condition = True

            if loop_condition:
                # Append source_cluster to min_cluster and update average centroid
                """print(
                                f"Source cluster: {source_cluster} \n Minimal cluster: {min_cluster}"
                )
                """
                min_cluster["regions"] += ref_cluster["regions"]
                # print(f"Updated minimal cluster: {min_cluster}")
                min_cluster["trim_mean_x_centroid"] = float(
                    stats.trim_mean(
                        [region["centroids"][0] for region in min_cluster["regions"]],
                        trim_cut,
                    )
                )
                # remove source_cluster
                clusters.remove(ref_cluster)

    print(f"Number of clusters: {len(clusters)}")
    print(f"Clusters sizes: {[len(cluster["regions"]) for cluster in clusters]} ")
    """ Check consistency of types"""
    for cluster in clusters:
        check_type = True 
        cluster_type = cluster["regions"][0]["type"]
        for region in cluster["regions"]:
            if region["type"] != cluster_type:
                check_type = False 
                print(f"Inconsistency of type in clusters!")
                break
    input()

    
    relations = []
    # Assign relation to best fitting cluster element, this time based on x-centroid, taking into account that the target region should be matched to the closest (according to x-centroid) cluster to the LEFT (Western reading order!)
    source_clusters = list(filter(lambda x: x["type"] == source_region_type, clusters))
    for target_region in target_regions:
        # determine the best cluster for the target according to x-centroid and reading order left
        min_cluster = None
        for cluster in source_clusters:
            if cluster["trim_mean_x_centroid"] < target_region["centroids"][0]:
                if min_cluster is None:
                    min_cluster = cluster
                else:
                    if abs(
                        target_region["centroids"][0] - cluster["trim_mean_x_centroid"]
                    ) < abs(
                        target_region["centroids"][0]
                        - min_cluster["trim_mean_x_centroid"]
                    ):
                        min_cluster = cluster

        if min_cluster is None:  # there must be an error with clustering
            print(
                "An error has occurred in the clustering, finding no cluster of sources left from target, we will just use the horizontal position"
            )
            print(f"Problematic target: {target_region}")
            for cluster in clusters:
                if min_cluster is None:
                    min_cluster = cluster
                else:
                    if abs(
                        target_region["centroids"][0] - cluster["trim_mean_x_centroid"]
                    ) < abs(
                        target_region["centroids"][0]
                        - min_cluster["trim_mean_x_centroid"]
                    ):
                        min_cluster = cluster

        # best fit according to weigthed euclidean distance
        best_region = None
        for cluster_region in min_cluster["regions"]:
            if best_region is None:
                best_region = cluster_region
            else:
                if weighted_euclidean_distance(target_region["centroids"],cluster_region["centroids"]) < weighted_euclidean_distance(target_region["centroids"],best_region["centroids"]):
                    best_region = cluster_region
        # append the relation to the relations dictionary
        relations.append(
            {
                "type": relations_type,
                "source": best_region["region_id"],
                "target": target_region["region_id"],
            }
        )

    # Return the regions dictionary
    return relations



def weighted_euclidean_distance(p,q,w=[0.05,1]): # d_w = \sqrt(w_x*(p_x-q_x)^2 + ... )
    d = 0
    for i in range(len(p)):
        d += w[i]*pow((p[i]-q[i]),2)

    return math.sqrt(d)


def neighborhood_clustering_method(): # inspired by DBSCAN https://cdn.aaai.org/KDD/1996/KDD96-037.pdf
    # TO BE CONTINUED

    pass 