<script lang="ts">
  import { Button } from "$lib/components/ui/button";
  import { sleep } from "$lib/utils.ts";
  import {
    Command,
    CommandItem,
    CommandList,
  } from "$lib/components/ui/command";
  import {
    CommandEmpty,
    CommandGroup,
  } from "$lib/components/ui/command/index.js";
  import { search } from "$lib/api";
  import { writable } from "svelte/store";
  import CustomSearchInput from "$lib/components/custom-search-input.svelte";
  import { type SearchResponse } from "$lib/types/search/searchApiResponse.ts";
  import {
    type CourseSearchResult,
    generateCourseSearchResults,
  } from "$lib/types/search/searchResults.ts";
  import { Popover, PopoverContent, Trigger } from "$lib/components/ui/popover";
  import { ChevronsUpDown } from "@lucide/svelte";
  import type { CourseReference } from "$lib/types/course";
    import { addCourse } from "$lib/takenCoursesStore";

  let open = $state(false);
  let numOptions = 20;
  let searchQuery = $state("");
  let triggerRef = $state<HTMLButtonElement>(null!);
  let selectedCourse: CourseSearchResult;
  let courses = writable<CourseSearchResult[]>([]);

  interface Props {
    status: string;
  }

  let {
    status = $bindable(),
  }: Props = $props();

  $effect(() => {
    updateSuggestions(searchQuery);
  });

  async function querySettled(query: string): Promise<boolean> {
    await sleep(500);
    return query === searchQuery;
  }

  async function updateSuggestions(query: string) {
    if (!(await querySettled(query))) {
      return;
    }

    if (query.length <= 0) {
      $courses = [];
      return;
    }

    const response = await search(searchQuery);
    const data: SearchResponse = await response.json();

    const rawCourses = data.courses;

    $courses = generateCourseSearchResults(rawCourses).slice(0, numOptions);
  }

  async function courseSuggestionSelected(result: CourseSearchResult) {
    try {
      //set status
      status = "Loading...";

      //close search
      open = false;

      let courseReference: CourseReference = {
        subjects: result.subjects,
        course_number: result.course_number,
      }
      addCourse(courseReference);
      status = "";
    } catch (e) {
      status = "there was an error adding the course";
      console.log(e);
    }
  }

  function closeAndFocusTrigger() {
    //close dropdown
    open = false;

    //add to courses
    courseSuggestionSelected(selectedCourse);
  }
</script>

<Popover bind:open>
  <Trigger bind:ref={triggerRef}>
    {#snippet child({ props })}
      <Button
        variant="outline"
        class="w-[400px] justify-between"
        {...props}
        role="combobox"
        aria-expanded={open}
      >
        Search courses to add...
        <ChevronsUpDown class="ml-2 size-4 shrink-0 opacity-50" />
      </Button>
    {/snippet}
  </Trigger>
  <PopoverContent class="w-[400px] p-0">
    <Command>
      <CustomSearchInput
        placeholder="Search courses..."
        bind:value={searchQuery}
      />
      <CommandList>
        <CommandEmpty>No course found.</CommandEmpty>
        <CommandGroup>
          {#each $courses as course}
            <CommandItem
              value={course.course_id}
              onSelect={() => {
                selectedCourse = course;
                closeAndFocusTrigger();
              }}
            >
              {course.subjects.join("/") + " " + course.course_number}
            </CommandItem>
          {/each}
        </CommandGroup>
      </CommandList>
    </Command>
  </PopoverContent>
</Popover>
