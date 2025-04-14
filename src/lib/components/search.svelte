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

    interface Props {
        wide?: boolean;
        fake?: boolean;
    }

    let { wide = false, fake = false }: Props = $props();

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

        const rawCourses = data.courses
        const rawSubjects = data.subjects
        const rawInstructors = data.instructors

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

<Button
        variant="outline"
        class={cn(
		"text-muted-foreground relative w-full justify-start text-sm sm:pr-12", wide ? "lg:w-[45rem] md:w-96" : "lg:w-80 md:w-40"
	)}
        onclick={() => {
            $searchModalOpen = true;
            searchQuery = "";
        }}
>
    <span class="hidden lg:inline-flex">Search courses, departments... </span>
    <span class="inline-flex lg:hidden">Search...</span>
    <kbd
            class="bg-muted pointer-events-none absolute right-1.5 top-2 hidden h-5 select-none items-center gap-1 rounded border px-1.5 font-mono text-[10px] font-medium opacity-100 sm:flex"
    >
        <CtrlCmd />K
    </kbd>
</Button>
{#if !fake}
    <Command.Dialog bind:open={$searchModalOpen}>
        <CustomSearchInput placeholder="Search courses, departments..." bind:value={searchQuery} />
        <Command.List>
            {#if $results.length <= 0 }
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
