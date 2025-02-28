"""
Script to generate OI Research Clusters Network
given a JSON input
"""

import csv
import json
from pyvis.network import Network
import networkx as nx


def csv2dict(csv_filename):  # dumps a CSV into dictionary with main property "items"
    f = open(csv_filename, "r")
    reader = csv.DictReader(f)
    d = {"items": []}
    for row in reader:
        d["items"].append(row)
    return d


def json2dict(fn):
    # Import json file
    with open(fn, "r") as f:
        dictionary = json.load(f)
        return dictionary


def new_node(net, node_id, label, color, value, title):
    return net.add_node(node_id, label=label, color=color, value=value, title=title)


def OINetworkGeneration(data):
    net = nx.Graph()
    # node attributes
    nodes_colors = {
        "orpheus": "#99001C",
        "cluster": "#d1ad65",
        "project": "#c14834",
        "researcher": "#f8f7f4",
    }

    nodes_values = {"orpheus": 500, "cluster": 250, "project": 100, "researcher": 25}

    # Generate nodes
    for item in data:
        title = (
            """
		<body>
		<h3> <a href='"""
            + item["url"]
            + """'>"""
            + item["label"]
            + """</a></h3>
		<p>"""
            + item["description"]
            + """</p>
		<a href='"""
            + item["url"]
            + """'><img src='"""
            + item["img_url"]
            + """' width=200px heigth=100px> </a>
		</body>
		"""
        )
        new_node(
            net,
            item["id"],
            item["label"],
            nodes_colors[item["type"]],
            nodes_values[item["type"]],
            title,
        )

    # Generate edges
    for item in data:
        if item["parent"] != "":
            if "|" in item["parent"]:
                splitted = item["parent"].split("|")
                for cluster in splitted:
                    net.add_edge(item["id"], cluster, weight=10)
            else:
                net.add_edge(item["id"], item["parent"], weight=10)

    # Return the generated network
    return net


def pyvis_visualization(net, net_filename):
    layout = nx.spring_layout(net)
    visualization = Network(
        height="600px",
        width="1200px",
        bgcolor="#1C1A19",
        font_color="#f8f7f4",
        directed=False,
        select_menu=False,
        filter_menu=False,
        notebook=False,
    )

    visualization.from_nx(net)
    visualization.toggle_physics(False)
    # visualization.show_buttons(filter_=["nodes", "physics"])

    options = """
			var options = {
					"configure": {
						"enabled": false
							},
					"edges": {
						"color": {
						"inherit": false
						},
					"smooth": false
					},
					"nodes": {
						"font": {
							"size": 14,
							"align": "center",
							"face": "sans"
						}
					},
					"physics": {
						"forceAtlas2Based": {
						"gravitationalConstant": -200000,
						"springLength": 1,
						"springConstant": 1.0,
						"avoidOverlap": 1.0,
						"damping":0

							},
					"maxVelocity": 1,
					"minVelocity": 0.25
						}
					}
				"""
    visualization.set_options(options)
    visualization.save_graph(net_filename + ".html")


# Import data
input_csv = "./input.csv"
data = csv2dict(input_csv)["items"]

net = OINetworkGeneration(data)

network_dict = nx.node_link_data(net, edges="edges")
network_file = open("output.json", "w")
json.dump(network_dict, network_file, indent=2)

pyvis_visualization(net, "output")
