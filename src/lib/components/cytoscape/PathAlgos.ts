export function getNonCompoundNodes(cy: cytoscape.Core | undefined) {
    return cy?.nodes().filter(function (node) {
        return node.data('type') !== 'compound';
    });
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

export function clearPath(cy: cytoscape.Core | undefined, myTip: any) {
    cy?.nodes().removeClass('highlighted-nodes');
    cy?.elements().removeClass('faded');
    cy?.edges().removeClass('highlighted-edges');
    myTip?.destroy();
}

