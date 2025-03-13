<script lang="ts">
    import  {Button} from "$lib/components/ui/button";
    import {cn, sleep} from "$lib/utils.ts";
    import * as Command from "$lib/components/ui/command/index.js";
    import CtrlCmd from "$lib/components/CtrlCmd.svelte";
    import { search } from "$lib/api";
    import { writable } from "svelte/store";
    import CustomSearchInput from "$lib/components/CustomSearchInput.svelte";
    import {
        courseSearchResponseToIdentifier,
        type SearchResponse
    } from "$lib/types/search/searchApiResponse.ts";
    import {Book, School, User} from "lucide-svelte";
    import {searchModalOpen} from "$lib/searchModalStore.ts";
    import {
        type CourseSearchResult,
        generateCourseSearchResults,
        generateInstructorSearchResults,
        generateSubjectSearchResults,
        type InstructorSearchResult,
        type SubjectSearchResult
    } from "$lib/types/search/searchResults.ts";
    import {goto} from "$app/navigation";
    import {toast} from "svelte-sonner";

    interface Props {
        wide?: boolean;
        fake?: boolean;
    }

    let { wide = false, fake = false }: Props = $props();

    let courses = writable<CourseSearchResult[]>([]);
    let subjects = writable<SubjectSearchResult[]>([]);
    let instructors = writable<InstructorSearchResult[]>([]);

    let shiftDown = $state(false);

    $effect(() => {
        updateSuggestions(searchQuery);
    });

    $effect(() => {
        if ($searchModalOpen) {
            toast.message("Tip", {
                description: "Hold shift to open course details directly.",
                duration: 3000,
                cancel: {
                    label: "Hide",
                    onClick: () => {
                        toast.dismiss();
                    }
                }
            })
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
            $courses = [];
            $subjects = [];
            $instructors = [];
            return
        }

        const response = await search(searchQuery)
        const data: SearchResponse = await response.json()

        const rawCourses = data.courses
        const rawSubjects = data.subjects
        const rawInstructors = data.instructors

        $courses = generateCourseSearchResults(rawCourses)
        $subjects = generateSubjectSearchResults(rawSubjects)
        $instructors = generateInstructorSearchResults(rawInstructors)
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

    function suggestionSelected(href: string) {
        goto(href);
        $searchModalOpen = false;
    }

    function courseSuggestionSelected(result: CourseSearchResult) {
        if (shiftDown) {
            goto(result.href);
        } else {
            goto(Object.values(result.explorerHref)[0]); // TODO change via dialog or something
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
            {#if $courses.length <= 0 && $subjects.length <= 0 && $instructors.length <= 0}
            <div class="py-6 text-center text-sm">No results found.</div>
            {/if}
            {#if $courses.length > 0}
                <Command.Group heading="Courses">
                    {#each $courses as suggestion }
                        <Command.Item
                                onSelect={() => {
                                    courseSuggestionSelected(suggestion)
                                }}
                        >
                        <Book class="mr-3 h-4 w-4" />
                        <div>
                            <p>{suggestion.course_title}</p>
                            <p class="text-xs">{courseSearchResponseToIdentifier(suggestion)}</p>
                            </div>
                        </Command.Item>
                    {/each}
                </Command.Group>
                <Command.Separator />
            {/if}
            {#if $subjects.length > 0}
                <Command.Group heading="Departments">
                    {#each $subjects as suggestion }
                        <Command.Item
                                onSelect={() => {
                                    suggestionSelected(suggestion.href)
                                }}
                        >
                            <School class="mr-3 h-4 w-4" />
                            <span>{suggestion.name}</span>
                        </Command.Item>
                    {/each}
                </Command.Group>
                <Command.Separator />
            {/if}
            {#if $instructors.length > 0}
                <Command.Group heading="Instructors">
                    {#each $instructors as suggestion }
                        <Command.Item
                                onSelect={() => {
                                    suggestionSelected(suggestion.href)
                                }}
                        >
                            <User class="mr-3 h-4 w-4" />
                            <div>
                                <p class="truncate line-clamp-1">{suggestion.name}</p>
                                <p class="text-xs">{suggestion.position} &#x2022; {suggestion.department}</p>
                            </div>
                        </Command.Item>
                    {/each}
                </Command.Group>
            {/if}
        </Command.List>
    </Command.Dialog>
{/if}
