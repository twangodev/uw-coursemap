export function getNonCompoundNodes(cy: cytoscape.Core | undefined) {
    return cy?.nodes().filter(function (node) {
        return node.data('type') !== 'compound';
    });
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
        if (takenNodes.contains(node.incomers('node'))) {
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

