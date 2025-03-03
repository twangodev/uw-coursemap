<script lang="ts">
    import { onMount } from "svelte";
    import {Button} from "$lib/components/ui/button";
    import {cn} from "$lib/utils.ts";
    import * as Command from "$lib/components/ui/command/index.js";
    import CtrlCmd from "$lib/components/CtrlCmd.svelte";
    import { search } from "$lib/api";
    import { writable } from "svelte/store";
    import CustomSearchInput from "$lib/components/CustomSearchInput.svelte";
    import {
        type CourseSearchResponse, courseSearchResponseToIdentifier,
        type InstructorSearchResponse,
        type SearchResponse,
        type SubjectSearchResponse
    } from "$lib/types/searchResponse.ts";
    import {Book, School, User} from "lucide-svelte";

    export let wide = false;

    let open = false;

    $: searchQuery = "";
    let courses = writable<CourseSearchResponse[]>([]);
    let subjects = writable<SubjectSearchResponse[]>([]);
    let instructors = writable<InstructorSearchResponse[]>([]);
    $: updateSuggestions(searchQuery);

    async function updateSuggestions(query: string) {
        if (query.length <= 0) {
            $courses = [];
            return
        }

        const response = await search(searchQuery)
        const data: SearchResponse = await response.json()
        $courses = data.courses
        $subjects = data.subjects
        $instructors = data.instructors
        console.log($courses);
    }

    onMount(() => {
        function handleKeydown(e: KeyboardEvent) {
            if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
                e.preventDefault();
                open = true;
            }
        }
        document.addEventListener("keydown", handleKeydown);

        return () => {
            document.removeEventListener("keydown", handleKeydown);
        };
    });
</script>

<Button
        variant="outline"
        class={cn(
		"text-muted-foreground relative w-full justify-start text-sm sm:pr-12", wide ? "lg:w-[45rem] md:w-96" : "lg:w-80 md:w-40"
	)}
        on:click={() => (open = true)}
        {...$$restProps}
>
    <span class="hidden lg:inline-flex">Search courses, departments... </span>
    <span class="inline-flex lg:hidden">Search...</span>
    <kbd
            class="bg-muted pointer-events-none absolute right-1.5 top-2 hidden h-5 select-none items-center gap-1 rounded border px-1.5 font-mono text-[10px] font-medium opacity-100 sm:flex"
    >
        <CtrlCmd />K
    </kbd>
</Button>
<Command.Dialog bind:open>
    <CustomSearchInput placeholder="Search courses, departments..." bind:value={searchQuery} />
    <Command.List>
        <Command.Empty>No results found.</Command.Empty>
        {#if $courses.length > 0}
            <Command.Group heading="Courses">
                {#each $courses as suggestion }
                    <Command.Item>
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
                    <Command.Item>
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
                    <Command.Item>
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
