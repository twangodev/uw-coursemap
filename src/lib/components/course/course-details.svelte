<script lang="ts">
    import {BookOpen, CalendarRange, ClipboardCheck, Info} from "@lucide/svelte";
    import {Card, CardContent, CardHeader, CardTitle} from "$lib/components/ui/card/index.js";
    import type {Course} from "$lib/types/course.ts";
    import {cn} from "$lib/utils.ts";
    import {onMount} from "svelte";
    import ClampedParagraph from "../clamped-paragraph.svelte";

    interface Props {
        course: Course;
        selectedTerm: string | undefined;
    }

    let {
        course,
        selectedTerm
    }: Props = $props();

    function termsWithEnrollmentData(course: Course) {
        const allTerms = Object.keys(course?.term_data ?? {}).sort((a, b) => Number(a) - Number(b));
        return allTerms.filter(term => course.term_data[term]?.enrollment_data != null);
    }

    function getLatestEnrollmentData(course: Course) {
        const validTerms = termsWithEnrollmentData(course);
        if (!validTerms.length) return null;
        const latestTerm = validTerms[validTerms.length - 1];

        let candidateTerm = selectedTerm ?? latestTerm;
        return course.term_data[candidateTerm]?.enrollment_data ?? course.term_data[latestTerm].enrollment_data;
    }

    const getCreditCount = (course: Course) => {
        const creditCount = getLatestEnrollmentData(course)?.credit_count;
        if (!creditCount) {
            return "Not Reported";
        }

        if (creditCount[0] === creditCount[1]) {
            return `${creditCount[0]}`;
        } else {
            return `${creditCount[0]} to ${creditCount[1]}`;
        }
    }

    const getNormallyOffered = (course: Course) => {
        return getLatestEnrollmentData(course)?.typically_offered ?? "Not Reported";
    }

    let descriptionElement: HTMLParagraphElement
    let showToggle = $state(false)
    let expandDescription = $state(false);

    function checkOverflow() {
        if (!descriptionElement) return;
        showToggle = descriptionElement.scrollHeight > descriptionElement.clientHeight;
    }

    function toggleExpandDescription() {
        expandDescription = !expandDescription;
    }

    onMount(() => {
        checkOverflow();
        window.addEventListener('resize', checkOverflow);
    });

    $effect(() => {
        checkOverflow();
    });

</script>

<div class="space-y-4 mt-2 lg:col-span-3">
    <Card>
        <CardHeader
                class="flex flex-row items-center justify-between space-y-0 pb-2"
        >
            <CardTitle class="text-base font-medium">Course Description</CardTitle>
            <Info class="text-muted-foreground h-4 w-4"/>
        </CardHeader>
        <CardContent>
            <ClampedParagraph
                clampAmount={5}
                class="text-sm break-words"
            >
                {course.description}
            </ClampedParagraph>
        </CardContent>
        <CardHeader
                class="flex flex-row items-center justify-between space-y-0 pb-2"
        >
            <CardTitle class="text-base font-medium">Prerequisties</CardTitle>
            <BookOpen class="text-muted-foreground h-4 w-4"/>
        </CardHeader>
        <CardContent>
            <ClampedParagraph
                clampAmount={3}
                class="text-sm break-words"
            >
                {course.prerequisites.prerequisites_text}
            </ClampedParagraph>
        </CardContent>
        <div class="flex flex-row space-x-4">
            <div class="flex-1">
                <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle class="text-base font-medium">Credits</CardTitle>
                    <ClipboardCheck class="text-muted-foreground h-4 w-4"/>
                </CardHeader>
                <CardContent>
                    <p class="text-sm break-words">{getCreditCount(course)}</p>
                </CardContent>
            </div>
            <div class="flex-1">
                <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle class="text-base font-medium">Offered</CardTitle>
                    <CalendarRange class="text-muted-foreground h-4 w-4"/>
                </CardHeader>
                <CardContent>
                    <p class="text-sm break-words">{getNormallyOffered(course)}</p>
                </CardContent>
            </div>
        </div>
    </Card>
</div>