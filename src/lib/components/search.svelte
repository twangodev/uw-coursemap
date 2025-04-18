<script lang="ts">
    import  {Button} from "$lib/components/ui/button";
    import {cn, sleep} from "$lib/utils.ts";
    import * as Command from "$lib/components/ui/command/index.js";
    import CtrlCmd from "$lib/components/ctrl-cmd.svelte";
    import {getRandomCourses, search} from "$lib/api";
    import { writable } from "svelte/store";
    import CustomSearchInput from "$lib/components/custom-search-input.svelte";
    import {
        searchResponseToIdentifier,
        type SearchResponse
    } from "$lib/types/search/searchApiResponse.ts";
    import {Book, School, User} from "lucide-svelte";
    import {searchModalOpen} from "$lib/searchModalStore.ts";
    import {
        combineSearchResults,
        type CourseSearchResult,
        generateCourseSearchResults,
        generateSubjectSearchResults,
        type InstructorSearchResult,
        type SubjectSearchResult, type UnifiedSearchResponse
    } from "$lib/types/search/searchResults.ts";
    import {goto} from "$app/navigation";
    import {toast} from "svelte-sonner";
    import { page } from "$app/stores";
    import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
    import { Filter } from "lucide-svelte";

    export interface SearchBarOptions {
        showCourses: boolean;
        showDepartments: boolean;
        showInstructors: boolean;
    }
    interface Props {
        wide?: boolean;
        fake?: boolean;
    }
    let props: Props = $props();
    let wide = props.wide ?? false;
    let fake = props.fake ?? false;

    const filterOptions = [
        { id: 'COURSES', label: 'Courses' },
        { id: 'DEPARTMENTS', label: 'Departments' },
        { id: 'INSTRUCTORS', label: 'Instructors' }
    ];
    // from the url it determines whether to show courses, departments, or instructors
    // I honestly hate using the url for this but b/c there can be multiple "fake" search bars the
    // real search bar is not always the first one in the DOM so we can't just use a prop to determine this
    let showOptionsQuery = $derived($page.url.searchParams.get('searchShowOptions')?.toUpperCase() ?? '');
    let showOptions = $derived<SearchBarOptions>({
        showCourses: showOptionsQuery ? showOptionsQuery.includes("COURSES"): true,
        showDepartments: showOptionsQuery ? showOptionsQuery.includes("DEPARTMENTS") : true,
        showInstructors: showOptionsQuery ? showOptionsQuery.includes("INSTRUCTORS") : true 
    })
    
    let selectedOptions = $state<string[]>(
        $page.url.searchParams.get('searchShowOptions')?.split(',')
            .map(opt => opt.toUpperCase())
            .filter(opt => ['COURSES', 'DEPARTMENTS', 'INSTRUCTORS'].includes(opt)) ?? 
        ['COURSES', 'DEPARTMENTS', 'INSTRUCTORS']
    );

    function updateSearchOptions(options: string[]) {
        const params = new URLSearchParams($page.url.searchParams);
        const currentPath = $page.url.pathname;

        // Prevent removing all options
        if (options.length === 0) {
            return;
        }

        // Update URL with new options
        params.set('searchShowOptions', options.join(','));
        goto(`${currentPath}?${params.toString()}`, { keepFocus: true });
        updateSuggestions(searchQuery);
    }

    function handleOptionToggle(option: string, checked: boolean) {
        if (checked && !selectedOptions.includes(option)) {
            selectedOptions = [...selectedOptions, option];
        } else if (!checked && selectedOptions.length > 1) {
            selectedOptions = selectedOptions.filter(opt => opt !== option);
        }
        updateSearchOptions(selectedOptions);
    }

    let placeholderString = $derived((() => {
        let options = [];
        if (showOptions.showCourses) options.push("courses")
        if (showOptions.showDepartments) options.push("departments")
        if (showOptions.showInstructors) options.push("instructors")
        return `Search ${options.join(", ")}...`
    })());

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
        return []
    })

    $effect(() => {
        if ($searchModalOpen && !fake) {
            toast.message("Tip", {
                description: "Hold shift to open course graph directly.",
                duration: 3000,
                cancel: {
                    label: "Hide",
                    onClick: () => {
                        toast.dismiss();
                    }
                }
            });
        }
    })

    async function querySettled(query: string) : Promise<boolean> {
        await sleep(500);
        return query === searchQuery;
    }

    async function updateSuggestions(query: string) {
        if (!await querySettled(query)) {
            return;
        }

        if (query.length <= 0) {
            $results = []
            return
        }

        const response = await search(searchQuery)
        const data: SearchResponse = await response.json()

        // Filter results before combining them
        const rawCourses = showOptions.showCourses ? data.courses : []
        const rawSubjects = showOptions.showDepartments ? data.subjects : []
        const rawInstructors = showOptions.showInstructors ? data.instructors : []

        $results = combineSearchResults(
            rawCourses,
            rawSubjects,
            rawInstructors
        )

    }

    function handleKeydown(e: KeyboardEvent) {
        if (fake) return;
        if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
            e.preventDefault();
            searchQuery = "";

            $searchModalOpen = !$searchModalOpen;
        }
        shiftDown = e.shiftKey
    }

    function handleKeyUp(e: KeyboardEvent) {
        shiftDown = e.shiftKey
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

<svelte:document onkeydown={handleKeydown} onkeyup={handleKeyUp}/>

<div class="flex gap-0">
    <DropdownMenu.Root>
        <DropdownMenu.Trigger>
            <Button variant="outline" size="icon" class="shrink-0 rounded-r-none border-r-0">
                <Filter class="h-4 w-4" />
                <span class="sr-only">Filter search</span>
            </Button>
        </DropdownMenu.Trigger>
        <DropdownMenu.Content align="start" class="w-48">
            <DropdownMenu.Label>Filter Search</DropdownMenu.Label>
                <DropdownMenu.Separator />
                    {#each filterOptions as option}
                        <DropdownMenu.CheckboxItem
                            checked={selectedOptions.includes(option.id)}
                            onCheckedChange={(checked) => handleOptionToggle(option.id, checked)}
                        >
                            {option.label}
                        </DropdownMenu.CheckboxItem>
                    {/each}
        </DropdownMenu.Content>
    </DropdownMenu.Root>

    <Button
        variant="outline"
        class={cn(
        "text-muted-foreground relative w-full justify-start text-sm sm:pr-12 rounded-l-none", wide ? "lg:w-[45rem] md:w-96" : "lg:w-90 md:w-40"
    )}
        onclick={() => {
            $searchModalOpen = true;
            searchQuery = "";
        }}
    >
    <span class="hidden lg:inline-flex">{placeholderString}</span>
    <span class="inline-flex lg:hidden">Search...</span>
    <kbd
            class="bg-muted pointer-events-none absolute right-1.5 top-2 hidden h-5 select-none items-center gap-1 rounded border px-1.5 font-mono text-[10px] font-medium opacity-100 sm:flex"
    >
        <CtrlCmd />K
    </kbd>
    </Button>
</div>

{#if !fake}
<Command.Dialog bind:open={$searchModalOpen}>
    <CustomSearchInput placeholder={placeholderString} bind:value={searchQuery} />
    
    <Command.List>
        <!-- TODO: Add way to generate random departments and instructors -->
        {#if $results.length <= 0}
            {#if showOptions.showCourses}
                {#await randomCourses}
                    <div class="py-6 text-center text-sm">No results found.</div>
                {:then randomCourses}
                <Command.Group heading="Random Courses">
                    {#each randomCourses as suggestion }
                        <Command.Item
                                onSelect={() => {
                                    courseSuggestionSelected(suggestion)
                                }}
                        >
                            <Book class="mr-3 h-4 w-4" />
                            <div>
                                <p>{suggestion.course_title}</p>
                                <p class="text-xs">{searchResponseToIdentifier({
                                    type: "course",
                                    data: suggestion
                                })}</p>
                            </div>
                        </Command.Item>
                    {/each}
                </Command.Group>
                {:catch error}
                    <div class="py-6 text-center text-sm">Error loading random courses.</div>
                {/await}
                {:else}
                <div class="py-6 text-center text-sm">No results found.</div>
                {/if}
            {/if}
            {#if $results.length > 0}
            <Command.Group heading="Results">
                                    {#each $results as suggestion}
                    <Command.Item onSelect={() => handleSuggestionSelect(suggestion)}>
                        <!-- Render icon based on type -->
                        {#if suggestion.type === 'course'}
                            <Book class="mr-3 h-4 w-4" />
                        {:else if suggestion.type === 'subject'}
                            <School class="mr-3 h-4 w-4" />
                        {:else if suggestion.type === 'instructor'}
                            <User class="mr-3 h-4 w-4" />
                        {/if}
                        <div>
                            {#if suggestion.type === 'course'}
                                <p>{getCourseTitle(suggestion)}</p>
                                <p class="text-xs">{searchResponseToIdentifier(suggestion)}</p>
                            {:else if suggestion.type === 'subject'}
                                <span>{getSubjectTitle(suggestion)}</span>
                            {:else if suggestion.type === 'instructor'}
                                <p class="truncate line-clamp-1">{getInstructorName(suggestion)}</p>
                                <p class="text-xs">{getInstructorDetail(suggestion)}</p>
                            {/if}
                        </div>
                    </Command.Item>
                {/each}
            </Command.Group>
        {/if}

        </Command.List>
    </Command.Dialog>
{/if}
