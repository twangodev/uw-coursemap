<script lang="ts">
    import cytoscape from "cytoscape";
    import cytoscapeFcose from "cytoscape-fcose"
    import tippy from "tippy.js";
    import cytoscapePopper from "cytoscape-popper";
    import {Progress} from "$lib/components/ui/progress";
    import {cn} from "$lib/utils.ts";
    import {type Course} from "$lib/types/course.ts";
    import { fetchCourse, fetchGraphData} from "./FetchData";
    import { getStyles } from "./Styles";
    import { FcoseLayout } from "./Layout";
    import SideControls from "./SideControls.svelte";
    import CourseSheet from "./CourseSheet.svelte";
    import { clearPath, highlightPath } from "./PathAlgos";

    interface Props {
        url: string;
        styleUrl: string;
    }

    let { url, styleUrl }: Props = $props();
    let sheetOpen = $state(false);
    let progress = $state({
        text: "Loading Graph...",
        number: 10,
    })

    let cy: cytoscape.Core | undefined = $state()
    let elementsAreDraggable = $state(false);

    const isDesktop = () => window.matchMedia('(min-width: 768px)').matches;

    let selectedCourse = $state<Course | undefined>();

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
    function destroyTip() {
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

        // if you want to use the other layout, just uncomment the one below and comment the other one
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
            highlightPath(cy, targetNode);
        });

        cy.on('mouseout', 'node', function (event) {
            clearPath(cy, destroyTip);
        });

        cy.on('tap', 'node', async function (event) {
            const targetNode = event.target;
            if (targetNode?.data('type') === 'compound') {
                return;
            }

            if (isDesktop()) {
                selectedCourse = undefined;
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
<CourseSheet {cy} bind:sheetOpen {selectedCourse} {destroyTip}/>