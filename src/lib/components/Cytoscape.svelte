<script lang="ts">
    import {onMount} from "svelte";
    import cytoscape from "cytoscape";
    import cytoscapeFcose from "cytoscape-fcose"

    export let courseData: cytoscape.ElementDefinition[]
    export let cytoscapeStyles: cytoscape.Stylesheet[]

    let cy: cytoscape.Core;

    onMount(() => {

        console.log(courseData)
        cytoscape.use(cytoscapeFcose);

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

    })

</script>
<div id="cy" class="h-full"></div>