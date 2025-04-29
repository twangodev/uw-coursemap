<script lang="ts">
    import * as Carousel from "$lib/components/ui/carousel/index.js";
    import {
        type Course,
        type CourseReference,
        courseReferenceToCourse
    } from "$lib/types/course.ts";
    import CourseCard from "$lib/components/course-carousel/course-card.svelte";

    interface Props {
        courses: Course[];
    }

    let { courses }: Props = $props();
</script>
{#if courses.length === 0}
    <p>No courses found</p>
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
