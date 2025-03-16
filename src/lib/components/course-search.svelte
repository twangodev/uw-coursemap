<script lang="ts">
    import  {Button} from "$lib/components/ui/button";
    import {cn, sleep} from "$lib/utils.ts";
    import * as Command from "$lib/components/ui/command/index.js";
    import { search } from "$lib/api";
    import { writable } from "svelte/store";
    import CustomSearchInput from "$lib/components/custom-search-input.svelte";
    import {
        courseSearchResponseToIdentifier,
        type SearchResponse
    } from "$lib/types/search/searchApiResponse.ts";
    import {Book, School, User} from "lucide-svelte";
    import {
        type CourseSearchResult,
        generateCourseSearchResults,
    } from "$lib/types/search/searchResults.ts";
    import {getCourse} from "$lib/api.ts";
    import {setData} from "$lib/localStorage.ts";

    let searchOpen = $state(false);

    //save the taken courses
    function saveData(){
        setData("takenCourses", takenCourses);
    }

    interface Props {
        takenCourses: Array<any>;
        status: string;
    }

    let { 
        takenCourses = $bindable(),
        status = $bindable()
    }: Props = $props();

    let courses = writable<CourseSearchResult[]>([]);

    $effect(() => {
        updateSuggestions(searchQuery);
    });

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
            return
        }

        const response = await search(searchQuery)
        const data: SearchResponse = await response.json()

        const rawCourses = data.courses

        $courses = generateCourseSearchResults(rawCourses)
    }

    async function courseSuggestionSelected(result: CourseSearchResult) {
        try{
            //close search
            searchOpen = false;

            //parse course ID, compssci_ece_252
            let courseIDParts = result.course_id.split("_");
            let courseID = courseIDParts.slice(-2).join("");
            
            //get course data from API
            let courseData = await getCourse(courseID);
            
            //check if it is a duplicate
            let duplicate = false;
            for(let takenCourse of takenCourses){
                if(
                    takenCourse["course_reference"]["course_number"] == courseData["course_reference"]["course_number"] &&
                    takenCourse["course_title"] == courseData["course_title"]
                ){
                    console.log("Course is a duplicate:", courseData["course_title"]);
                    duplicate = true;
                }
            }

            //add to list (only if not duplicate)
            if(!duplicate){
                takenCourses.push(courseData);
                takenCourses = takenCourses; //force update
        
                //save to local storage
                saveData();
            }
            else{
                status = "course was not added due to being a duplicate";
            }
        }
        catch(e){
            status = "there was an error adding the course";
            console.log(e);
        }
    }

    let searchQuery = $state("");

</script>

<Button
    variant="outline"
    class={cn(
		"text-muted-foreground relative w-full justify-start text-sm sm:pr-12", 
        "lg:w-80 md:w-40"
	)}
        onclick={() => {
            searchOpen = true;
            searchQuery = "";
        }}
>
    <span class="hidden lg:inline-flex">Search courses... </span>
    <span class="inline-flex lg:hidden">Add course...</span>
</Button>

<Command.Dialog bind:open={searchOpen}>
    <CustomSearchInput placeholder="Search courses, departments..." bind:value={searchQuery} />
    <Command.List>
        {#if $courses.length <= 0}
            <div class="py-6 text-center text-sm">Enter something into the search bar pwetty pweese</div>
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
            <Command.Separator/>
        {/if}
    </Command.List>
</Command.Dialog>
