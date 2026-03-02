
  const container = document.getElementById('graph-container'),
        width = container.offsetWidth,
        height = container.offsetHeight;

  const svg = d3.select(container).append("svg")
      .attr("width", "100%")
      .attr("height", "100%")
      .attr("viewBox", `0 0 ${width} ${height}`)
      .attr("preserveAspectRatio", "xMidYMid meet");

  const g = svg.append("g");
  const tooltip = d3.select("body").append("div").attr("id", "tooltip").attr("class", "tooltip");

  const color = d3.scaleOrdinal()
      .domain(["center", "secondary", "tertiary"])
      .range(["#d4a373", "#a3b18a", "#f2e8cf"]);

  const nodes = [
    { id: "interface", label: "interface", group: "center", description: "gathering-together" },
    { id: "scale", label: "scale", group: "secondary", description: "position" },
    { id: "agent", label: "agent", group: "secondary", description: "participant" },
    { id: "world", label: "world", group: "secondary", description: "situation" },
    { id: "generalization", label: "generalization", group: "secondary", description: "terms of engagement" },
    { id: "standard", label: "standard", group: "tertiary", description: "measure" },
    { id: "ideology", label: "ideology", group: "tertiary", description: "capture" },
    { id: "norm", label: "norm", group: "tertiary", description: "topology of meaning" },
    { id: "system", label: "system", group: "tertiary", description: "topology of interrelation" },
    { id: "continuous phenomena", label: "continuous phenomena", group: "tertiary", description: "materiality" },
    { id: "discrete phenomena", label: "discrete phenomena", group: "tertiary", description: "virtuality" },
    { id: "boundary conditions", label: "boundary conditions", group: "tertiary", description: "black boxes" }
  ];

  const links = [
    { source: "interface", target: "scale" },
    { source: "interface", target: "agent" },
    { source: "interface", target: "world" },
    { source: "interface", target: "generalization" },
    { source: "generalization", target: "standard" },
    { source: "generalization", target: "ideology" },
    { source: "world", target: "norm" },
    { source: "world", target: "system" },
    { source: "scale", target: "continuous phenomena" },
    { source: "scale", target: "discrete phenomena" },
    { source: "scale", target: "boundary conditions" },
    { source: "norm", target: "ideology" },
    { source: "agent", target: "boundary conditions" },
    { source: "discrete phenomena", target: "system" },
    { source: "discrete phenomena", target: "standard" },
    { source: "continuous phenomena", target: "world" }
  ];

  const simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id(d => d.id).distance(110))
      .force("charge", d3.forceManyBody().strength(-600))
      .force("collide", d3.forceCollide().radius(d => 10 + 20))
      .force("center", d3.forceCenter((width / 2), (height / 2)));

  const link = g.append("g").attr("class", "links")
      .selectAll("line").data(links).enter().append("line")
      .attr("class", "link").attr("stroke-width", 1.5);

  const node = g.append("g").attr("class", "nodes")
      .selectAll("g").data(nodes).enter().append("g")
      .attr("class", "node")
      .on("mouseover", (event, d) => {
        // Highlight connected links and nodes
        link
          .style("stroke-opacity", l => 
            (l.source.id === d.id || l.target.id === d.id) ? 1 : 0.1);
            
        tooltip.transition().duration(200).style("opacity", 0.9);
        tooltip.html(`<strong>${d.label}</strong><br/>${d.description}`)
               .style("left", (event.pageX + 5) + "px")
               .style("top", (event.pageY - 28) + "px");
      })
      .on("mouseout", () => {
        // Restore all links to normal opacity
        link.style("stroke-opacity", 0.6);
        
        tooltip.transition().duration(500).style("opacity", 0);
      })
      .call(d3.drag()
          .on("start", (event, d) => { if (!event.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
          .on("drag", (event, d) => { d.fx = event.x; d.fy = event.y; })
          .on("end", (event, d) => { if (!event.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }));

  node.append("circle").attr("r", 10).attr("fill", d => color(d.group));
  node.append("text").attr("dx", 12).attr("dy", ".35em")
      .text(d => d.label)
      .style("font-size", d => d.id === "interface" ? "20px" : "14px")
      .style("font-weight", "normal");

  simulation.on("tick", () => {
    link.attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);
    node.attr("transform", d => `translate(${d.x},${d.y})`);
  });
