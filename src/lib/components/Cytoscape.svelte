<script lang="ts">
    import {onMount} from "svelte";
    import cytoscape, {type Stylesheet} from "cytoscape";
    import cytoscapeFcose from "cytoscape-fcose"
    import tippy from "tippy.js";
    import cytoscapePopper from "cytoscape-popper";

    export let url: string
    export let styleUrl: string

    let cy: cytoscape.Core;

    function tippyFactory(ref: any, content: any) {
        // Since tippy constructor requires DOM element/elements, create a placeholder
        const dummyDomEle = document.createElement('div');

        return tippy(dummyDomEle, {
            getReferenceClientRect: ref.getBoundingClientRect,
            trigger: 'manual', // mandatory
            content: content,
            arrow: true,
            placement: 'bottom',
            hideOnClick: true,
            sticky: "reference",
            interactive: true,
            appendTo: document.body // or append dummyDomEle to document.body
        })
    }

    let myTip: any;

    function setTip(newTip: any) {
        myTip?.destroy();
        myTip = newTip;
    }


    onMount(async () => {

        let response = await fetch(url);
        let courseData = await response.json();

        let styleResponse = await fetch(styleUrl);
        let styleData = await styleResponse.json();

        let cytoscapeStyles : Stylesheet[] = [
            {
                selector: 'node',
                style: {
                    'label': (data: { data: (key: string) => any, id: () => string }): string => {
                        return data.data('label') || data.id();
                    },
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'background-color': '#757575',
                }
            },
            {
                selector: '.highlighted-nodes',
                style: {
                    'border-width': 1,
                    'border-color': '#000',
                    'border-style': 'solid',
                }
            },
            {
                selector: '.faded',
                style: {
                    'opacity': 0.25,
                    'text-opacity': 0.25,
                }
            },
            {
                selector: '*',
                style: {
                    'transition-property': 'opacity',
                    'transition-duration': 0.2,
                }
            },
            {
                selector: 'node[type="compound"]',
                style: {
                    'text-valign': 'top',
                    'border-width': 0,
                    'background-opacity': 0,
                    label: '',
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 1,
                    'line-color': '#000',
                    'curve-style': 'straight',
                    'target-arrow-color': '#000',
                    'target-arrow-shape': 'triangle',
                    'source-distance-from-node': 5,
                    'target-distance-from-node': 5,
                    'text-wrap': 'wrap',
                    'font-size': 10,
                }
            },
            {
                selector: '.highlighted-edges',
                    style: {
                        'width': 2,
                    }
            }
        ]

        const styles = styleData.map(item => {
            const [parent, color] = Object.entries(item)[0];
            return {
                selector: `node[parent="${parent}"]`,
                style: {
                    'background-color': color,
                },
            };
        });

        cytoscapeStyles = cytoscapeStyles.concat(styles);


        console.log(cytoscapeStyles)


        cytoscape.use(cytoscapeFcose);
        cytoscape.use(cytoscapePopper(tippyFactory))

        let cytoscapeLayout: cytoscape.BreadthFirstLayoutOptions = {
            name: 'breadthfirst',
            directed: true,
            padding: 10,
        }

        cy = cytoscape({
            container: document.getElementById('cy'),
            elements: courseData,
            style: cytoscapeStyles,
            layout: cytoscapeLayout,
            minZoom: 0.01,
            maxZoom: 2,
            motionBlur: true,
        });

        let newCytoscapeLayout: cytoscapeFcose.FcoseLayoutOptions = {
            name: 'fcose',
            quality: 'proof', // 'draft', 'default' or 'proof'
            animate: true, // Whether to animate the layout
            animationDuration: 1000, // Duration of the animation in milliseconds
            animationEasing: 'ease-out', // Easing of the animation
            fit: true, // Whether to fit the viewport to the graph
            padding: 30, // Padding around the layout
            nodeDimensionsIncludeLabels: true, // Excludes the label when calculating node bounding boxes for the layout algorithm
            uniformNodeDimensions: true, // Specifies whether the node dimensions should be uniform
            packComponents: true, // Pack connected components - usually for graphs with multiple components
            nodeRepulsion: 40000, // Node repulsion (non overlapping) multiplier
            idealEdgeLength: 50, // Ideal edge (non nested) length
            edgeElasticity: 0.45, // Divisor to compute edge forces
            nestingFactor: 1, // Nesting factor (multiplier) to compute ideal edge length for nested edges
            gravity: 1000,
            gravityRangeCompound: 1,
            gravityCompound: 100,
            gravityRange: 1.5,
            initialEnergyOnIncremental: 1,
            randomize: true, // Whether to randomize the initial positions of nodes
            // fixedNodeConstraint: [
            //     {
            //         nodeId: '300',
            //         position: {x: -100, y: 0}
            //     },
            //     {
            //         nodeId: '400',
            //         position: {x: 100, y: 0}
            //     }
            // ],
            // alignmentConstraint: {
            //     vertical: [],
            //     horizontal: [
            //         ['221', '222'],
            //         ['300', '400']
            //     ]
            // },
            // relativePlacementConstraint: [
            //     {left: '200', right: '300', gap: 100},
            //     {left: '221', right: '222', gap: 200},
            // ]
        }

        cy.layout(newCytoscapeLayout).run();

        cy.on('mouseover', 'node', function (event) {
            const targetNode = event.target;
            highlightPath(targetNode);
        });

        cy.on('mouseout', 'node', function (event) {
            cy.nodes().removeClass('highlighted-nodes');
            cy.elements().removeClass('faded');
            cy.edges().removeClass('highlighted-edges');
            myTip?.destroy();
        });

        cy.on('click', 'node', async function (event) {
            const targetNode = event.target;
            if (targetNode?.data('type') === 'compound') {
                return;
            }

            let tip = targetNode.popper({
                content: () => {
                    let div = document.createElement('div');
                    div.innerHTML = `
                        <div class="bg-black text-white p-2 rounded-lg">
                            <h1 class="text-lg font-semibold">${targetNode.id()}</h1>
                            <p class="text-sm">${targetNode.data('description')}</p>
                        </div>
                    `;
                    return div;
                },
            });
            tip.show();

            setTip(tip);
        });

        function getNonCompoundNodes() {
            return cy.nodes().filter(function (node) {
                return node.data('type') !== 'compound';
            });
        }

        function highlightPath(node: cytoscape.NodeSingular) {

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

            const nonCompoundNodes = getNonCompoundNodes();

            const fadeNodes = nonCompoundNodes.difference(highlightedNodes);
            const fadeEdges = cy.edges().difference(highlightedEdges);
            fadeNodes.addClass('faded');
            fadeEdges.addClass('faded');

        }

    })

</script>
<div id="cy" class="h-full"></div>