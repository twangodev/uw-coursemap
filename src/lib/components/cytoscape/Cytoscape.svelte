<script lang="ts">
    import {onMount} from "svelte";
    import cytoscape, {type EdgeDefinition, type LayoutOptions, type NodeDefinition, type Position, type StylesheetStyle} from "cytoscape";
    import cytoscapeFcose from "cytoscape-fcose"
    import tippy from "tippy.js";
    import cytoscapePopper from "cytoscape-popper";
    import {Button} from "$lib/components/ui/button";
    import {LockKeyhole, LockKeyholeOpen, LucideFullscreen, LucideMinus, LucidePlus} from "lucide-svelte";
    import {Progress} from "$lib/components/ui/progress";
    import {cn} from "$lib/utils.ts";
    import {type Course, courseReferenceToString, sanitizeCourseToReferenceString} from "$lib/types/course.ts";
    import {Root, SheetContent, SheetDescription, SheetHeader, SheetTitle} from "$lib/components/ui/sheet";
    import {writable} from "svelte/store";
    import {Skeleton} from "$lib/components/ui/skeleton";
    import {Separator} from "$lib/components/ui/separator";
    import ArrowUpRight from "lucide-svelte/icons/arrow-up-right";
    import {ScrollArea} from "$lib/components/ui/scroll-area";
    import InstructorPreview from "$lib/components/instructor-preview/InstructorPreview.svelte";
    import {apiFetch} from "$lib/api.ts";
    import {Tooltip, TooltipContent, TooltipProvider, TooltipTrigger} from "../ui/tooltip";
    import ELK, { type ElkNode } from 'elkjs/lib/elk.bundled.js'
    import {page} from "$app/state";
    import {pushState} from "$app/navigation";
    import { fetchCourse, fetchGraphData, getEdgeData, getNodeData } from "./Data";
    import { getStyles } from "./Styles";
    import { FcoseLayout, generateLayeredLayout } from "./Layout";
    import SideControls from "./SideControls.svelte";
    import Sheet from "./Sheet.svelte";

    let focus = $derived(page.url.searchParams.get('focus'));

    interface Props {
        url: string;
        styleUrl: string;
    }

    let { url, styleUrl }: Props = $props();
    let sheetOpen = $state(false);

    function getNonCompoundNodes() {
        return cy?.nodes().filter(function (node) {
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

        const fadeNodes = nonCompoundNodes?.difference(highlightedNodes);
        const fadeEdges = cy?.edges().difference(highlightedEdges);
        fadeNodes?.addClass('faded');
        fadeEdges?.addClass('faded');
    }

    $effect(() => {
        (async () => {
            if (cy && focus) {
                sheetOpen = true;
                let response = await apiFetch(`/course/${focus}.json`);
                let course = await response.json();
                selectedCourse = course

                let id = courseReferenceToString(course.course_reference);
                let node = cy.$id(id)

                cy.zoom({
                    level: 1.5,
                    renderedPosition: node.renderedPosition()
                });
                cy.zoom(1.5);
                cy.center(node);
                clearPath();
                highlightPath(node);
            }
        })();
    })

    $effect(() => {
        if (cy && selectedCourse) {
            let courseId = sanitizeCourseToReferenceString(selectedCourse.course_reference);

            if (sheetOpen) {
                page.url.searchParams.set('focus', courseId);

            } else {
                page.url.searchParams.delete('focus');
            }

            pushState(page.url, page.state);
        }
    })

    let progress = $state({
        text: "Loading Graph...",
        number: 10,
    })

    let cy: cytoscape.Core | undefined = $state()
    let elementsAreDraggable = $state(false);

    const isDesktop = () => window.matchMedia('(min-width: 768px)').matches;

    let selectedCourse = $state<Course | null>(null);

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
        
        let courseData = await fetchGraphData(url); 

        progress = {
            text: "Styling Graph...",
            number: 50,
        }

        let cytoscapeStyles = getStyles(styleUrl);

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

        // let newCytoscapeLayout = await generateLayeredLayout(courseData);
        let newCytoscapeLayout = FcoseLayout;
        
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
                selectedCourse = null;
                sheetOpen = true;

                selectedCourse = await fetchCourse(targetNode.id())
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

    <SideControls bind:elementsAreDraggable {cy}/>
</div>
<Sheet bind:sheetOpen {selectedCourse}/>