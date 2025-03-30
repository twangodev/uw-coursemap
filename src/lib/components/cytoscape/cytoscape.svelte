<script lang="ts">
    import cytoscape, {
        type Collection,
        type EdgeCollection,
        type ElementDefinition,
        type StylesheetStyle
    } from "cytoscape";
    import cytoscapeFcose from "cytoscape-fcose"
    import tippy from "tippy.js";
    import cytoscapePopper from "cytoscape-popper";
    import {Progress} from "$lib/components/ui/progress";
    import {cn} from "$lib/utils.ts";
    import {courseReferenceToString, sanitizeCourseToReferenceString, type Course} from "$lib/types/course.ts";
    import {fetchCourse, fetchGraphData} from "./graph-data.ts";
    import {getStyleData, getStyles, type StyleEntry} from "./graph-styles.ts";
    import SideControls from "./side-controls.svelte";
    import CourseDrawer from "./course-drawer.svelte";
    import {clearPath, highlightPath, markNextCourses} from "./paths.ts";
    import {searchModalOpen} from "$lib/searchModalStore.ts";
    import {generateFcoseLayout, generateLayeredLayout, LayoutType} from "$lib/components/cytoscape/graph-layout.ts";
    import {page} from "$app/state";
    import {mode} from "mode-watcher";
    import {getTextColor, getTextOutlineColor} from "$lib/theme.ts";
    import Legend from "./legend.svelte";
    import { onMount } from "svelte";
    import { getData } from "$lib/localStorage.ts";

    interface Props {
        url: string;
        styleUrl: string;
    }

    let takenCourses: (undefined | string)[] = [];
    //load data
    onMount(() => {
        // console.log("mounted")
        // console.log("data", getData("takenCourses"));
        takenCourses = getData("takenCourses").map((course: any) => {
            if (course.course_reference === undefined) {
                return;
            }

            return courseReferenceToString(course.course_reference);
        });
        // console.log("after", takenCourses);
    });

    let { url, styleUrl }: Props = $props();
    let sheetOpen = $state(false);
    let progress = $state({
        text: "Loading Graph...",
        number: 10,
    })
    let focus = $derived(page.url.searchParams.get('focus'));
    let courseData: ElementDefinition[] = $state([]);
    let cytoscapeStyleData: StyleEntry[] = $state([]);
    let cytoscapeStyles: StylesheetStyle[] = $state([]);

    let layoutType : LayoutType = $state(LayoutType.LAYERED);

    searchModalOpen.subscribe((isOpen) => {
        if (isOpen) {
            sheetOpen = false;
        }
    });

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

        courseData = await fetchGraphData(url);

        progress = {
            text: "Styling Graph...",
            number: 50,
        }


        cytoscapeStyleData = await getStyleData(styleUrl);
        cytoscapeStyles = await getStyles(cytoscapeStyleData, $mode);

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
        let layout = await computeLayout(layoutType, courseData);

        progress = {
            text: "Graph Loaded",
            number: 99,
        }

        cy = cytoscape({
            container: document.getElementById('cy'),
            elements: courseData,
            style: cytoscapeStyles,
            layout: layout,
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

    async function computeLayout(layoutType: LayoutType, courseData: ElementDefinition[]) {
        if (!cy) {
            return;
        }

        if (layoutType === LayoutType.GROUPED) {
            cy.layout(generateFcoseLayout(focus)).run();
        } else {
            await (async () => {
                cy.layout(await generateLayeredLayout(focus, courseData)).run();
            })();
        }
    }

    $effect(() => {
        if (!cy || !takenCourses) {
            return;
        }

        cy.nodes().forEach((node: cytoscape.NodeSingular) => {
            if (takenCourses.includes(node.data("id"))) {
                node.addClass("taken-nodes");
            } else {
                node.removeClass("taken-nodes");
            }
        });

        // console.log("actually taken: ", takenCourses);
        markNextCourses(cy);
    })

    $effect(() => {
        computeLayout(layoutType, courseData);
    })

    $effect(() => {
        if (!cy) {
            return;
        }
        cy.style().selector('node').style({
            'color': getTextColor($mode),
            'text-outline-color': getTextOutlineColor($mode),
	        'text-outline-opacity': 1,
	        'text-outline-width': 1
        }).selector('.highlighted-nodes').style({
            'border-color': getTextColor($mode),
        }).selector('edge').style({
            'line-color': getTextColor($mode),
            'target-arrow-color': getTextColor($mode),
        }).selector('.taken-nodes').style({
            'color': "#008450",
        }).selector('.next-nodes').style({
            'color': "#EFB700",
        }).update()
    })

    let hiddenSubject = $state(null)

    let removedSubjectNodes: Collection | null

    function hide(subject: string | null) {
        // console.log(hiddenSubject);
        if (!cy) {
            return;
        }

        removedSubjectNodes?.restore()
        removedSubjectNodes = null

        if (subject) {
            removedSubjectNodes = cy.nodes(`[parent = "${subject}"]`).remove();
        }

        computeLayout(layoutType, courseData);
    }

    $effect(() => {
        if (!cy) {
            return;
        }

        hide(hiddenSubject);
    })


</script>
<div class="relative grow">
    <div class={cn("absolute inset-0 flex flex-col justify-center items-center space-y-4 transition-opacity", progress.number === 100 ? "opacity-0" : "")}>
        <p class="text-lg font-semibold">{progress.text}</p>
        <Progress class="w-[80%] md:w-[75%] lg:w-[30%]" value={progress.number}/>
    </div> <div id="cy" class={cn("w-full h-full transition-opacity", progress.number !== 100 ? "opacity-0" : "")}></div>

    <Legend styleEntries={cytoscapeStyleData} bind:hiddenSubject />
    <SideControls {cy} bind:elementsAreDraggable bind:layoutType/>
</div>
<CourseDrawer {cy} bind:sheetOpen {selectedCourse} {destroyTip}/>