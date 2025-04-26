<script lang="ts">
    import ContentWrapper from "$lib/components/content/content-wrapper.svelte";
    import {page} from '$app/state';
    import ContentH1 from "$lib/components/content/content-h1.svelte";
    import {type Course, courseReferenceStringToCourse, sanitizeCourseToReferenceString} from "$lib/types/course.ts";
    import {courseReferenceToString} from "$lib/types/course.js";
    import {
        ArrowUpRight,
        BookA,
        BookOpen,
        BookPlus,
        CalendarRange,
        CircleCheckBig,
        ClipboardCheck,
        Info,
        Users
    } from "lucide-svelte";
    import {calculateARate, calculateCompletionRate, calculateGradePointAverage} from "$lib/types/madgrades.ts";
    import Change from "$lib/components/change.svelte";
    import InstructorPreview from "$lib/components/instructor-preview/instructor-preview.svelte";
    import {type FullInstructorInformation, getFullInstructorInformation} from "$lib/types/instructor.ts";
    import GradeDataHorizontalBarChart from "$lib/components/charts/grade-data-horizontal-bar-chart.svelte";
    import CourseCarousel from "$lib/components/course-carousel/course-carousel.svelte";
    import ComboGradeDataStackedAreaChart from "$lib/components/charts/combo-grade-data-stacked-area-chart.svelte";
    import {apiFetch} from "$lib/api.ts";
    import {getLatestTermIdPromise, type Terms} from "$lib/types/terms.ts";
    import InstructorWordCloud from "$lib/components/charts/instructor-word-cloud.svelte";
    import TermSelector from "$lib/components/term-selector.svelte";
    import {Tabs, TabsContent, TabsList, TabsTrigger} from "$lib/components/ui/tabs";
    import {Card, CardContent, CardDescription, CardHeader, CardTitle} from "$lib/components/ui/card";
    import Cytoscape from "$lib/components/cytoscape/cytoscape.svelte";
    import {env} from "$env/dynamic/public";
    import { Button } from "$lib/components/ui/button";
    import {CourseHeader, CourseTabs} from "$lib/components/course";

    const PUBLIC_API_URL = env.PUBLIC_API_URL;

    let courseIdentifier = $derived(page.params.courseIdentifier);

    let course: Promise<Course> = $derived(courseReferenceStringToCourse(courseIdentifier));

    let terms: Promise<Terms> = (async () => {
        let termsData = await apiFetch(`/terms.json`)
        return await termsData.json()
    })();

    let selectedTerm: string | undefined = $state(undefined)

    let latestTerm = $derived.by(async () => {
        selectedTerm = String(await getLatestTermIdPromise(terms))
        return selectedTerm
    });

    let currentCourseIdentifier: string | null = null;



</script>

<ContentWrapper>
    {#await Promise.all([course, terms, latestTerm])}
        <p class="text-center">Loading...</p>
    {:then [course, terms]}
        <CourseHeader
            course={course}
            terms={terms}
            bind:selectedTerm={selectedTerm}
        />
        <CourseTabs
            course={course}
            terms={terms}
            bind:selectedTerm={selectedTerm}
        />

    {:catch error}
        <p class="text-red-600">Error loading course: {error.message}</p>
    {/await}
</ContentWrapper>