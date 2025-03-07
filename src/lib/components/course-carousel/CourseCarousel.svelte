<script lang="ts">
    import * as Carousel from "$lib/components/ui/carousel/index.js";
    import {
        type Course,
        type CourseReference,
        courseReferenceToCourse
    } from "$lib/types/course.ts";
    import CourseCard from "$lib/components/course-carousel/CourseCard.svelte";
    import {onMount} from "svelte";
    import CourseCardSkeleton from "$lib/components/course-carousel/CourseCardSkeleton.svelte";

    interface Props {
        courseReferences: CourseReference[];
    }

    let { courseReferences }: Props = $props();

    let courses: Course[] = $state(); // Array to hold fetched Course objects
    let loadedCourses = $state(false);

    onMount(async () => {
        loadedCourses = false;
        courses = await Promise.all(
            courseReferences.map(async (courseReference) => {
                return await courseReferenceToCourse(courseReference);
            })
        );
        loadedCourses = true;
    });
</script>
{#if courseReferences.length === 0}
    <p>No courses found</p>
{:else}
    {#if !loadedCourses}
        <Carousel.Root>
            <Carousel.Content>
                {#each courseReferences as _}
                    <Carousel.Item class="basis-1/2 md:basis-1/3 lg:basis-1/4">
                            <CourseCardSkeleton />
                    </Carousel.Item>
                {/each}
            </Carousel.Content>
        </Carousel.Root>
    {:else}
        <Carousel.Root>
            <Carousel.Content>
                {#each courses as course}
                    <Carousel.Item class="basis-1/2 md:basis-1/3 lg:basis-1/4">
                        <CourseCard {course} />
                    </Carousel.Item>
                {/each}
            </Carousel.Content>
            <Carousel.Previous />
            <Carousel.Next />
        </Carousel.Root>
    {/if}
{/if}
