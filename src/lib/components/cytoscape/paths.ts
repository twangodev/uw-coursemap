export function getNonCompoundNodes(cy: cytoscape.Core | undefined) {
    return cy?.nodes().filter(function (node) {
        return node.data('type') !== 'compound';
    });
}

export function getPredecessorsNotTaken(cy: cytoscape.Core | undefined, node: cytoscape.NodeSingular, takenCourses: (undefined | string)[]): Array<string> {
    // console.log(node);
    let visited = new Set<cytoscape.NodeSingular>();
    dfs(node, visited, takenCourses);
    console.log("array", Array.from(visited.values()).map((node) => node.data("id")));
    return Array.from(visited.values().map(node => node.data("id")));
}

function dfs(node: cytoscape.NodeSingular, visited: Set<cytoscape.NodeSingular>, takenCourses: (undefined | string)[]) {
    visited.add(node);
    if (!takenCourses.includes(node.data('id'))) {
        const incomers = node.incomers('node');
        incomers.forEach((incomer) => {
            if (!visited.has(incomer)) {
                dfs(incomer, visited, takenCourses);
            }
        });
    }
}

export function markNextCourses(cy: cytoscape.Core | undefined) {
    if (!cy) {
        return;
    }
    const takenNodes = cy.nodes('.taken-nodes');

    const outgoingNodes = new Set<cytoscape.NodeSingular>();
    takenNodes.forEach(
        (node) => {
            const nextNodes = node.outgoers('node');
            nextNodes.forEach((node) => {
                outgoingNodes.add(node)});
        }
    )
    // console.log("Taken Nodes: ", takenNodes.forEach((node) => console.log(node.data('id'))));
    outgoingNodes.forEach((node) => {
        if (!takenNodes.intersection(node).empty()) return;
        // console.log("Node: ", node.data('id'));
        // console.log("Incomers: ", node.incomers('node').map((node) => node.data('id')));
        // console.log("is Contains: ", takenNodes.contains(node.incomers()));
        const incomers = node.incomers('node');
        let allIncomersTaken = true;
        incomers.forEach((incomer) => {
            if (!takenNodes.contains(incomer)) {
                allIncomersTaken = false;
            }
        })

        if (allIncomersTaken) {
            node.addClass('next-nodes');
        }
        // else console.log(node.data('id'));
    })
}

export function highlightPath(cy: cytoscape.Core | undefined, node: cytoscape.NodeSingular) {
    if (node.data('type') === 'compound') {
        return;
    }

    const incomingNodes = node.predecessors('node').union(node);
    const incomingEdges = node.predecessors('edge');

    const outgoingNodes = node.outgoers('node').union(node);
    const outgoingEdges = node.outgoers('edge');

    const highlightedNodes = incomingNodes.union(outgoingNodes);
    const highlightedEdges = incomingEdges.union(outgoingEdges);

    highlightedNodes.addClass('highlighted-nodes');
    highlightedEdges.addClass('highlighted-edges');

    const nonCompoundNodes = getNonCompoundNodes(cy);

    const fadeNodes = nonCompoundNodes?.difference(highlightedNodes);
    const fadeEdges = cy?.edges().difference(highlightedEdges);
    fadeNodes?.addClass('faded');
    fadeEdges?.addClass('faded');
}

export function clearPath(cy: cytoscape.Core | undefined, destroyTip: () => void) {
    cy?.nodes().removeClass('highlighted-nodes');
    cy?.elements().removeClass('faded');
    cy?.edges().removeClass('highlighted-edges');
    destroyTip();
}

