<script lang="ts">
  import { Button } from "$lib/components/ui/button";
  import { cn, sleep } from "$lib/utils.ts";
  import CtrlCmd from "$lib/components/ctrl-cmd.svelte";
  import { getRandomCourses, search } from "$lib/api";
  import { writable } from "svelte/store";
  import CustomSearchInput from "$lib/components/custom-search-input.svelte";
  import {
    searchResponseToIdentifier,
    type SearchResponse,
  } from "$lib/types/search/searchApiResponse.ts";
  import { Book, School, User } from "@lucide/svelte";
  import {
    allOptionsAreDisabled,
    filterOptions,
    searchModalOpen,
    searchOptions,
    type SearchBarOptions,
  } from "$lib/searchModalStore.ts";
  import {
    combineSearchResults,
    type CourseSearchResult,
    generateCourseSearchResults,
    type InstructorSearchResult,
    type SubjectSearchResult,
    type UnifiedSearchResponse,
  } from "$lib/types/search/searchResults.ts";
  import { goto } from "$app/navigation";
  import { toast } from "svelte-sonner";
  import { Filter } from "@lucide/svelte";
  import {
    DropdownMenu,
    DropdownMenuTrigger,
    DropdownMenuContent,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuCheckboxItem,
  } from "$lib/components/ui/dropdown-menu";
  import {
    CommandDialog,
    CommandGroup,
    CommandItem,
    CommandList,
  } from "$lib/components/ui/command";

  interface Props {
    wide?: boolean;
    fake?: boolean;
  }
  let props: Props = $props();
  let wide = props.wide ?? false;
  let fake = props.fake ?? false;

  function updateSearchOptions(options: SearchBarOptions) {
    // Prevent removing all options
    if (allOptionsAreDisabled(options)) {
      toast.message("At least one option must be selected", {
        description: "Please select at least one search option.",
        duration: 3000,
        cancel: {
          label: "Hide",
          onClick: () => {
            toast.dismiss();
          },
        },
      });
      return;
    }

    // update the selected options
    $searchOptions = options;
    updateSuggestions(searchQuery);
  }

  function handleOptionToggle(
    option: keyof SearchBarOptions,
    checked: boolean,
  ) {
    const updatedOptions: SearchBarOptions = {
      ...$searchOptions,
      [option]: checked,
    };
    updateSearchOptions(updatedOptions);
  }

  let placeholderString = $derived(
    (() => {
      let options = [];
      if ($searchOptions.showCourses) options.push("courses");
      if ($searchOptions.showDepartments) options.push("departments");
      if ($searchOptions.showInstructors) options.push("instructors");
      return `Search ${options.join(", ")}...`;
    })(),
  );

  let results = writable<UnifiedSearchResponse[]>([]);
  let shiftDown = $state(false);

  $effect(() => {
    updateSuggestions(searchQuery);
  });

  let randomCourses = $derived.by(async () => {
    if ($searchModalOpen && !fake) {
      const response = await getRandomCourses();
      const data: CourseSearchResult[] = await response.json();
      return generateCourseSearchResults(data);
    }
    return [];
  });

  $effect(() => {
    if ($searchModalOpen && !fake) {
      toast.message("Tip", {
        description: "Hold shift to open course graph directly.",
        duration: 3000,
        cancel: {
          label: "Hide",
          onClick: () => {
            toast.dismiss();
          },
        },
      });
    }
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
      $results = [];
      return;
    }

    const response = await search(searchQuery);
    const data: SearchResponse = await response.json();

    // Filter results before combining them
    const rawCourses = $searchOptions.showCourses ? data.courses : [];
    const rawSubjects = $searchOptions.showDepartments ? data.subjects : [];
    const rawInstructors = $searchOptions.showInstructors
      ? data.instructors
      : [];

    $results = combineSearchResults(rawCourses, rawSubjects, rawInstructors);
  }

  function handleKeydown(e: KeyboardEvent) {
    if (fake) return;
    if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      searchQuery = "";

      $searchModalOpen = !$searchModalOpen;
    }
    shiftDown = e.shiftKey;
  }

  function handleKeyUp(e: KeyboardEvent) {
    shiftDown = e.shiftKey;
  }

  function getCourseTitle(suggestion: UnifiedSearchResponse) {
    if (suggestion.type === "course") {
      const courseSearch = suggestion.data as CourseSearchResult;
      return courseSearch.course_title;
    }
    return "";
  }

  function getSubjectTitle(suggestion: UnifiedSearchResponse) {
    if (suggestion.type === "subject") {
      const subjectSearch = suggestion.data as SubjectSearchResult;
      return subjectSearch.name;
    }
    return "";
  }

  function getInstructorName(suggestion: UnifiedSearchResponse) {
    if (suggestion.type === "instructor") {
      const instructorSearch = suggestion.data as InstructorSearchResult;
      return instructorSearch.name;
    }
    return "";
  }

  function getInstructorDetail(suggestion: UnifiedSearchResponse) {
    if (suggestion.type === "instructor") {
      const instructorSearch = suggestion.data as InstructorSearchResult;
      return `${instructorSearch.position ?? "Position Unknown"} • ${instructorSearch.department ?? "Department Unknown"}`;
    }
    return "";
  }

  function handleSuggestionSelect(suggestion: UnifiedSearchResponse) {
    if (suggestion.type === "course") {
      const courseSearch = suggestion.data as CourseSearchResult;
      if (shiftDown) {
        goto(Object.values(courseSearch.explorerHref)[0]);
      } else {
        goto(courseSearch.href);
      }
    } else {
      goto(suggestion.data.href);
    }
    $searchModalOpen = false;
  }

  function courseSuggestionSelected(result: CourseSearchResult) {
    if (shiftDown) {
      goto(Object.values(result.explorerHref)[0]); // TODO change via dialog or something
    } else {
      goto(result.href);
    }
    $searchModalOpen = false;
  }

  let searchQuery = $state("");
</script>

<svelte:document onkeydown={handleKeydown} onkeyup={handleKeyUp} />

<div class="flex gap-0">
  <DropdownMenu>
    <DropdownMenuTrigger>
      <Button
        variant="outline"
        size="icon"
        class="shrink-0 rounded-r-none border-r-0"
      >
        <Filter class="h-4 w-4" />
        <span class="sr-only">Filter search</span>
      </Button>
    </DropdownMenuTrigger>
    <DropdownMenuContent align="start" class="w-48">
      <DropdownMenuLabel>Filter Search</DropdownMenuLabel>
      <DropdownMenuSeparator />
      {#each filterOptions as option}
        <DropdownMenuCheckboxItem
          checked={$searchOptions[option.id]}
          onCheckedChange={(checked) => handleOptionToggle(option.id, checked)}
        >
          {option.label}
        </DropdownMenuCheckboxItem>
      {/each}
    </DropdownMenuContent>
  </DropdownMenu>

  <Button
    variant="outline"
    class={cn(
      "text-muted-foreground relative w-full justify-start rounded-l-none text-sm sm:pr-12",
      wide ? "md:w-96 lg:w-[45rem]" : "md:w-40 lg:w-90",
    )}
    onclick={() => {
      $searchModalOpen = true;
      searchQuery = "";
    }}
  >
    <span class="hidden lg:inline-flex">{placeholderString}</span>
    <span class="inline-flex lg:hidden">Search...</span>
    <kbd
      class="bg-muted pointer-events-none absolute top-2 right-1.5 hidden h-5 items-center gap-1 rounded border px-1.5 font-mono text-[10px] font-medium opacity-100 select-none sm:flex"
    >
      <CtrlCmd />K
    </kbd>
  </Button>
</div>

{#if !fake}
  <CommandDialog bind:open={$searchModalOpen}>
    <CustomSearchInput
      placeholder={placeholderString}
      bind:value={searchQuery}
    />
    <CommandList>
      <!-- TODO: Add way to generate random departments and instructors -->
      {#if $results.length <= 0}
        {#if $searchOptions.showCourses}
          {#await randomCourses}
            <div class="py-6 text-center text-sm">No results found.</div>
          {:then randomCourses}
            <CommandGroup heading="Random Courses">
              {#each randomCourses as suggestion}
                <CommandItem
                  onSelect={() => {
                    courseSuggestionSelected(suggestion);
                  }}
                >
                  <Book class="mr-3 h-4 w-4" />
                  <div>
                    <p>{suggestion.course_title}</p>
                    <p class="text-xs">
                      {searchResponseToIdentifier({
                        type: "course",
                        data: suggestion,
                      })}
                    </p>
                  </div>
                </CommandItem>
              {/each}
            </CommandGroup>
          {:catch error}
            <div class="py-6 text-center text-sm">
              Error loading random courses.
            </div>
          {/await}
        {:else}
          <div class="py-6 text-center text-sm">No results found.</div>
        {/if}
      {/if}
      {#if $results.length > 0}
        <CommandGroup heading="Results">
          {#each $results as suggestion}
            <CommandItem onSelect={() => handleSuggestionSelect(suggestion)}>
              <!-- Render icon based on type -->
              {#if suggestion.type === "course"}
                <Book class="mr-3 h-4 w-4" />
              {:else if suggestion.type === "subject"}
                <School class="mr-3 h-4 w-4" />
              {:else if suggestion.type === "instructor"}
                <User class="mr-3 h-4 w-4" />
              {/if}
              <div>
                {#if suggestion.type === "course"}
                  <p>{getCourseTitle(suggestion)}</p>
                  <p class="text-xs">
                    {searchResponseToIdentifier(suggestion)}
                  </p>
                {:else if suggestion.type === "subject"}
                  <span>{getSubjectTitle(suggestion)}</span>
                {:else if suggestion.type === "instructor"}
                  <p class="line-clamp-1 truncate">
                    {getInstructorName(suggestion)}
                  </p>
                  <p class="text-xs">{getInstructorDetail(suggestion)}</p>
                {/if}
              </div>
            </CommandItem>
          {/each}
        </CommandGroup>
      {/if}
    </CommandList>
  </CommandDialog>
{/if}
