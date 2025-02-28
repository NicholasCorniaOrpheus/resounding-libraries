/* Main JavaScript code for rendering a vis.js network 

You will need to encode the data according to vis.js nodes and edges syntax.
For more information visit https://visjs.github.io/vis-network/docs/network/

*/

// initialize global variables.
var edges;
var nodes;
var allNodes;
var allEdges;
var nodeColors;
var originalNodes;
var network;
var container;
var options, data;
var filter = {
item : '',
property : '',
value : []
};

// This method is responsible for drawing the graph, returns the drawn network
function drawGraph() {
var container = document.getElementById('mynetwork');
};

// Load nodes, edges and options from JSON filename.

// Load Items function 
const loadItems = async (filename) => {
    try {
        const res = await fetch(filename);
        items = await res.json();
        return items;

    } catch (err) {
        console.error(err);
    }
};
// loading JSONs into JS objects
// const nodesJSON = loadItems('./nodes.json');
// const edgesJSON = loadItems('./edges.json');
const optionsJSON = loadItems('./options.json');

console.log(optionsJSON);
                  
// Collecting nodes and edges from json files.
 

