<script lang="ts">
    import * as Carousel from "$lib/components/ui/carousel/index.js";
    import {
        type Course,
        type CourseReference,
        courseReferenceToCourse
    } from "$lib/types/course.ts";
    import CourseCard from "$lib/components/course-carousel/CourseCard.svelte";
    import CourseCardSkeleton from "$lib/components/course-carousel/CourseCardSkeleton.svelte";

    interface Props {
        courseReferences: CourseReference[];
    }

    let { courseReferences }: Props = $props();

    let courses: Promise<Course[]> = $derived.by(() => {
        return Promise.all(courseReferences.map(courseReferenceToCourse));
    })

</script>
{#if courseReferences.length === 0}
    <p>No courses found</p>
{:else}
    <Carousel.Root>
        <Carousel.Content>
            {#await courses}
                {#each courseReferences as _}
                    <Carousel.Item class="basis-1/2 md:basis-1/3 lg:basis-1/4">
                            <CourseCardSkeleton />
                    </Carousel.Item>
                {/each}
            {:then courses}
                {#each courses as course}
                    <Carousel.Item class="basis-1/2 md:basis-1/3 lg:basis-1/4">
                        <CourseCard {course} />
                    </Carousel.Item>
                {/each}

            {:catch error}
                <p>{error.message}</p>
            {/await}
        </Carousel.Content>
        <Carousel.Previous />
        <Carousel.Next />
    </Carousel.Root>
{/if}
