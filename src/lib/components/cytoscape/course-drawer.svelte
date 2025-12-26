<script lang="ts">
  import { Skeleton } from "$lib/components/ui/skeleton";
  import {
    type Course,
    CourseUtils,
  } from "$lib/types/course.ts";
  import { Separator } from "$lib/components/ui/separator";
  import { Button } from "$lib/components/ui/button";
  import InstructorPreview from "../instructor-preview/instructor-preview.svelte";
  import { ArrowUpRight } from "@lucide/svelte";
  import { apiFetch } from "$lib/api";
  import { clearPath, highlightPath } from "./paths.ts";
  import { page } from "$app/state";
  import { pushState } from "$app/navigation";
  import type { Terms } from "$lib/types/terms.ts";
  import { onMount, tick } from "svelte";
  import {
    Drawer,
    DrawerContent,
    DrawerFooter,
    DrawerTitle,
  } from "$lib/components/ui/drawer";
  import {
    DrawerDescription,
    DrawerHeader,
  } from "$lib/components/ui/drawer/index.js";
  import ClampedParagraph from "../clamped-paragraph.svelte";
  import { localizeHref } from "$lib/paraglide/runtime";
  import { m } from "$lib/paraglide/messages";
  import { searchModalOpen } from "$lib/searchModalStore.ts";

  interface Props {
    cy: cytoscape.Core | undefined;
    destroyTip: () => void;
    allowFocusing: boolean;
  }

  let {
    cy,
    destroyTip,
    allowFocusing = true,
  }: Props = $props();
  let sheetOpen = $state(false);
  let selectedCourse: Course | undefined = $state(undefined);

  export const closeDrawer = function () {
    sheetOpen = false;
  }
  export const openDrawer = function () {
    sheetOpen = true;
  }
  export const setSelectedCourse = function (course: Course | undefined) {
    selectedCourse = course;
  }
  let focus = $derived(page.url.searchParams.get("focus"));

  let terms: Terms = $state({});
  let latestTerm = $derived(Object.keys(terms).sort().pop() ?? ""); // TODO Allow user to select term

  let instructors = $derived(
    selectedCourse == undefined ? [] : Object.entries(CourseUtils.getInstructorsWithEmail(selectedCourse, latestTerm)),
  );

  onMount(async () => {
    let termsData = await apiFetch(`/terms.json`);
    terms = await termsData.json();
  });

  searchModalOpen.subscribe((isOpen) => {
    if (isOpen) {
      sheetOpen = false;
    }
  });

  $effect(() => {
    (async () => {
      if (cy && focus) {
        let response = await apiFetch(`/course/${focus}.json`);
        let course = await response.json();

        let id = CourseUtils.courseReferenceToString(course.course_reference);
        let node = cy.$id(id);

        cy.animate({
          zoom: 2,
          center: {
            eles: node,
          },
          duration: 1000,
          easing: "ease-in-out",
          queue: true,
        });

        clearPath(cy, destroyTip);
        highlightPath(cy, node);

        sheetOpen = true;
        selectedCourse = course;
      }
    })();
  });

  $effect(() => {
    if (!cy || !allowFocusing) return;

    if (!sheetOpen) {
      focus = null;
    }
    
    if (sheetOpen) {
      if (selectedCourse) {
        let courseId = CourseUtils.courseReferenceToSanitizedString(
          selectedCourse.course_reference,
        );
        page.url.searchParams.set("focus", courseId);
      }
    } else {
      page.url.searchParams.delete("focus");
    }

    tick().then(() => {
      pushState(page.url, page.state);
    });
  });
</script>

<Drawer bind:open={sheetOpen} shouldScaleBackground>
  <DrawerContent class="mx-auto w-full max-w-sm">
    <DrawerHeader class="sticky">
      <DrawerTitle class="text-2xl">
        {#if selectedCourse}
          {CourseUtils.courseReferenceToString(selectedCourse.course_reference)}
        {:else}
          <Skeleton class="h-6 w-9/12" />
        {/if}
      </DrawerTitle>
      <div class="font-semibold">
        {#if selectedCourse}
          {selectedCourse.course_title}
        {:else}
          <Skeleton class="h-5 w-6/12" />
        {/if}
      </div>
      <DrawerDescription>
        {#if selectedCourse}
          <ClampedParagraph clampAmount={5}>
            {selectedCourse.description}
          </ClampedParagraph>
        {:else}
          <Skeleton class="h-5 w-6/12" />
        {/if}
      </DrawerDescription>
    </DrawerHeader>
    <div class="p-4 pb-0">
      {#if instructors}
        {#each instructors.slice(0, 3) as [name, email], index}
          {#if index === 0}
            <div class="mt-2 font-semibold">INSTRUCTORS</div>
            <Separator class="my-1" />
          {/if}
          <InstructorPreview
            instructor={{
              name: name,
              email: email ?? "",
              credentials: null,
              rmp_data: null,
              department: null,
              official_name: null,
              position: null,
              courses_taught: [],
              cumulative_grade_data: null,
            }}
          />
        {/each}
        {#if instructors.length > 3}
          <div class="flex justify-center">
            <span class="text-muted-foreground text-xs"
              >Showing 3 of {instructors.length} instructors.</span
            >
          </div>
        {/if}
      {/if}
    </div>

    {#if selectedCourse}
      <DrawerFooter>
        <Button
          href={localizeHref(`/courses/${CourseUtils.courseReferenceToSanitizedString(
            selectedCourse.course_reference,
          )}`)}
          target="_blank"
        >
          {m["course.drawer.viewCoursePage"]()}
          <ArrowUpRight class="h-4 w-4" />
        </Button>
      </DrawerFooter>
    {/if}
  </DrawerContent>
</Drawer>
