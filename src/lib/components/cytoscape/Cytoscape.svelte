<script lang="ts">
    import {onMount} from "svelte";
    import cytoscape, {
        type CollectionReturnValue,
        type LayoutOptions,
        type Position,
        type StylesheetStyle
    } from "cytoscape";
    import cytoscapeFcose from "cytoscape-fcose"
    import tippy from "tippy.js";
    import cytoscapePopper from "cytoscape-popper";
    import {Button} from "$lib/components/ui/button";
    import {LockKeyhole, LockKeyholeOpen, LucideFullscreen, LucideMinus, LucidePlus} from "lucide-svelte";
    import {Progress} from "$lib/components/ui/progress";
    import {cn} from "$lib/utils.ts";
    import {type Course, courseReferenceToString, sanitizeCourseToReferenceString} from "$lib/types/course.ts";
    import {writable} from "svelte/store";
    import {Skeleton} from "$lib/components/ui/skeleton";
    import {Separator} from "$lib/components/ui/separator";
    import {Root, SheetContent, SheetDescription, SheetHeader, SheetTitle} from "$lib/components/ui/sheet";
    import ArrowUpRight from "lucide-svelte/icons/arrow-up-right";
    import {ScrollArea} from "$lib/components/ui/scroll-area";
    import InstructorPreview from "$lib/components/instructor-preview/InstructorPreview.svelte";
    import {apiFetch} from "$lib/api.ts";
    import {Tooltip, TooltipContent, TooltipProvider, TooltipTrigger} from "../ui/tooltip";
    import ELK, { type ElkNode } from 'elkjs/lib/elk.bundled.js'
    import {page} from "$app/state";
    import {pushState} from "$app/navigation";
    import {searchModalOpen} from "$lib/searchModalStore.ts";

    let focus = $derived(page.url.searchParams.get('focus'));

    interface Props {
        url: string;
        styleUrl: string;
    }

    let { url, styleUrl }: Props = $props();
    let sheetOpen = writable(false);

    searchModalOpen.subscribe((b) => {
        if (b) {
            sheetOpen.set(false);
        }
    });

    function getNonCompoundNodes() {
        return cy?.nodes().filter(function (node) {
            return node.data('type') !== 'compound';
        });
    }

    function highlightPath(node: cytoscape.NodeSingular) {
        if (node.data('type') === 'compound') {
            return
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

        const fadeNodes = nonCompoundNodes?.difference(highlightedNodes);
        const fadeEdges = cy?.edges().difference(highlightedEdges);
        fadeNodes?.addClass('faded');
        fadeEdges?.addClass('faded');

        return highlightedNodes;
    }

    $effect(() => {
        (async () => {
            if (cy && focus) {
                let response = await apiFetch(`/course/${focus}.json`);
                let course = await response.json();

                let id = courseReferenceToString(course.course_reference);
                let node = cy.$id(id)


                cy.animate({
                    zoom: 2,
                    center: {
                        eles: node,
                    },
                    duration: 1000,
                    easing: 'ease-in-out',
                    queue: true
                });

                clearPath();
                highlightPath(node)

                $selectedCourse = course
                $sheetOpen = true;
            }
        })();
    })

    $effect(() => {
        if (cy && $selectedCourse) {
            let courseId = sanitizeCourseToReferenceString($selectedCourse.course_reference);

            if ($sheetOpen) {
                page.url.searchParams.set('focus', courseId);

            } else {
                page.url.searchParams.delete('focus');
            }

            pushState(page.url, page.state);
        }
    })

    type StyleData = {
        [parent: string]: string;
    };

    let progress = $state({
        text: "Loading Graph...",
        number: 10,
    })

    let isFullscreen = false;
    let cy: cytoscape.Core | undefined = $state()

    const toggleFullscreen = () => {
        if (!isFullscreen) {
            let element = document.getElementById('cy-container');
            element?.requestFullscreen();
        } else {
            document.exitFullscreen();
        }
        isFullscreen = !isFullscreen;
    };

    const zoomIn = () => {
        cy?.zoom(cy.zoom() + 0.1);
    };

    const zoomOut = () => {
        cy?.zoom(cy.zoom() - 0.1);
    };

    let elementsAreDraggable = $state(false);
    const toggleDraggableElements = () => {
        elementsAreDraggable = !elementsAreDraggable;
    }

    const isDesktop = () => window.matchMedia('(min-width: 768px)').matches;

    let selectedCourse = writable<Course | null>(null);

    async function fetchCourse(courseId: string) {
        let response = await apiFetch(`/course/${courseId.replaceAll(" ", "_").replaceAll("/", "_")}.json`);
        $selectedCourse = await response.json();
    }

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

    function clearPath() {
        cy?.nodes().removeClass('highlighted-nodes');
        cy?.elements().removeClass('faded');
        cy?.edges().removeClass('highlighted-edges');
        myTip?.destroy();
    }

    const loadGraph = async () => {

        progress = {
            text: "Fetching Graph Data...",
            number: 25,
        }

        let response = await fetch(url);
        let courseData = await response.json();
        courseData.forEach((item: any) => {
            item['pannable'] = true;
        });

        progress = {
            text: "Styling Graph...",
            number: 50,
        }

        let styleResponse = await fetch(styleUrl);
        let styleData: StyleData[] = await styleResponse.json();

        let cytoscapeStyles: StylesheetStyle[] = [
            {
                selector: 'node',
                style: {
                    'label': 'data(id)',
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
            },
            {
                selector: '.no-overlay',
                style: {
                    'overlay-padding': 0,
                    'overlay-opacity': 0,
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

        progress = {
            text: "Loading Layout...",
            number: 55,
        }

        cytoscape.use(cytoscapeFcose);

        progress = {
            text: "Loading Tooltips...",
            number: 60,
        };

        cytoscape.use(cytoscapePopper(tippyFactory));

        progress = {
            text: "Rendering Graph...",
            number: 65,
        };

        const elk = new ELK()
        const newLayout = {
            id: "root",
            layoutOptions: { 'elk.algorithm': 'layered' },
            children: (courseData.filter((item: any) => !("source" in item.data))).map((node: {data: {description: string, id: string, parent: string}}) => {
                return {
                    id: node.data.id,
                    width: node.data.id.length * 15,
                    height: 50 
                }
            }),
            edges: (courseData.filter((item: any) => ("source" in item.data))).map((node: {data: {source: string, target: string}}) => {
                return {
                    id: node.data.source + "-" + node.data.target,
                    sources: [node.data.source],
                    targets: [node.data.target],
                }
            })
        }
        
        const nodePos = await elk.layout(newLayout)
//         let newCytoscapeLayout: LayoutOptions = {
//             name: 'preset',

//             positions: Object.fromEntries(
//                 nodePos.children!.map((child) => [child.id, { x: child.x === undefined ? 0 : child.x, y: child.y === undefined ? 0 : child.y }])
//             ),            // (id: string) => {
//             //     let ele = nodePos.children!.filter(child => child.id === id)[0]
//             //     return {
//             //         x: ele.x,
//             //         y: ele.y
//             //     }
//             // }, // map of (node id) => (position obj); or function(node){ return somPos; }
//             zoom: undefined, // the zoom level to set (prob want fit = false if set)
//             pan: undefined, // the pan level to set (prob want fit = false if set)
//             fit: true, // whether to fit to viewport
//             padding: 30, // padding on fit
//         }

        let newCytoscapeLayout: cytoscapeFcose.FcoseLayoutOptions = {
            name: 'fcose',
            quality: 'proof', // 'draft', 'default' or 'proof'
            animate: !(focus), // Whether to animate the layout
            animationDuration: 1000, // Duration of the animation in milliseconds
            animationEasing: 'ease-out',
            fit: true, // Whether to fit the viewport to the graph
            padding: 30, // Padding around the layout
            nodeDimensionsIncludeLabels: true, // Excludes the label when calculating node bounding boxes for the layout algorithm
            uniformNodeDimensions: true, // Specifies whether the node dimensions should be uniform
            packComponents: true, // Pack connected components - usually for graphs with multiple components
            nodeRepulsion: 40000, // Node repulsion (non overlapping) multiplier
            idealEdgeLength: 60, // Ideal edge (non nested) length
            edgeElasticity: 0.002, // Divisor to compute edge forces
            nestingFactor: 1, // Nesting factor (multiplier) to compute ideal edge length for nested edges
            gravity: 1,
            gravityRangeCompound: 1,
            gravityCompound: 0.1,
            gravityRange: 1.5,
            initialEnergyOnIncremental: 0.1,
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

        progress = {
            text: "Graph Loaded",
            number: 99,
        }

        cy = cytoscape({
            container: document.getElementById('cy'),
            elements: courseData,
            style: cytoscapeStyles,
            layout: newCytoscapeLayout,
            minZoom: 0.01,
            maxZoom: 2,
            motionBlur: true,
        });

        cy.on('mouseover', 'node', function (event) {
            const targetNode = event.target;
            if (elementsAreDraggable) {
                targetNode.removeClass('no-overlay');
                targetNode.unpanify();
            } else {
                targetNode.addClass('no-overlay');
                targetNode.panify();
            }
            highlightPath(targetNode);
        });

        cy.on('mouseout', 'node', function (event) {
            clearPath();
        });

        cy.on('tap', 'node', async function (event) {
            const targetNode = event.target;
            if (targetNode?.data('type') === 'compound') {
                return;
            }

            if (isDesktop()) {
                $selectedCourse = null;
                $sheetOpen = true;

                fetchCourse(targetNode.id()).then(() => {
                });
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

        progress = {
            text: "Graph Loaded",
            number: 100,
        }




    };

    $effect(() => {
        if (url && styleUrl) {
            loadGraph()
        }
    });

</script>
<div class="relative grow" id="cy-container">
    <div class={cn("absolute inset-0 flex flex-col justify-center items-center space-y-4 transition-opacity", progress.number === 100 ? "opacity-0" : "")}>
        <p class="text-lg font-semibold">{progress.text}</p>
        <Progress class="w-[80%] md:w-[75%] lg:w-[30%]" value={progress.number}/>
    </div> <div id="cy" class={cn("w-full h-full transition-opacity", progress.number !== 100 ? "opacity-0" : "")}></div>

    <div class="absolute bottom-4 right-4 flex flex-col space-y-2">
        <TooltipProvider>
            <Tooltip>
                <TooltipTrigger>
                    <Button size="sm" variant="outline" class="h-8 w-8 px-0" onclick={toggleDraggableElements}>
                        {#if elementsAreDraggable}
                            <LockKeyholeOpen class="h-5 w-5" />
                        {:else}
                            <LockKeyhole class="h-5 w-5"/>
                        {/if}
                    </Button>
                </TooltipTrigger>
                <TooltipContent>
                    {#if elementsAreDraggable}
                        Lock Elements
                    {:else}
                        Unlock Elements
                    {/if}
                </TooltipContent>
            </Tooltip>
        </TooltipProvider>

        <Button size="sm" variant="outline" class="h-8 w-8 px-0" onclick={zoomIn}>
            <LucidePlus class="h-5 w-5"/>
        </Button>
        <!-- Zoom Out Button -->
        <Button  size="sm" variant="outline" class="h-8 w-8 px-0" onclick={zoomOut}>
            <LucideMinus class="h-5 w-5"/>
        </Button>

        <Button  size="sm" variant="outline" class="h-8 w-8 px-0" onclick={toggleFullscreen}>
            <LucideFullscreen class="h-5 w-5"/>
        </Button>
    </div>
</div>

<Root bind:open={$sheetOpen}>
    <SheetContent class="flex flex-col h-full">
        <SheetHeader class="sticky">
            <SheetTitle class="text-2xl">
                {#if $selectedCourse}
                    {courseReferenceToString($selectedCourse.course_reference)}
                {:else}
                    <Skeleton class="h-6 w-9/12"/>
                {/if}
            </SheetTitle>
        </SheetHeader>
        <ScrollArea class="flex-1 overflow-y-auto mr-1">
            <div class="font-semibold">
                {#if $selectedCourse}
                    {$selectedCourse.course_title}
                {:else}
                    <Skeleton class="h-5 w-6/12"/>
                {/if}
            </div>
            <Separator class="my-1"/>
            <SheetDescription>
                {#if $selectedCourse}
                    {$selectedCourse.description}
                {:else}
                    <Skeleton class="h-5 w-6/12"/>
                {/if}
            </SheetDescription>
            {#if $selectedCourse}
                {#each Object.entries($selectedCourse?.enrollment_data?.instructors ?? {}) as [name, email], index}
                    {#if index === 0}
                        <div class="font-semibold mt-2">INSTRUCTORS</div>
                        <Separator class="my-1" />
                    {/if}
                    <InstructorPreview instructor={{
                        name: name,
                        email: email,
                        credentials: null,
                        rmp_data: null,
                        department: null,
                        official_name: null,
                        position: null
                    }}/>
                {/each}
            {/if}
        </ScrollArea>
        {#if $selectedCourse}
            <Button class="sticky bottom-0" href="/courses/{sanitizeCourseToReferenceString($selectedCourse.course_reference)}" target="_blank">
                View Course Page
                <ArrowUpRight class="h-4 w-4"/>
            </Button>
        {/if}
    </SheetContent>
</Root>
