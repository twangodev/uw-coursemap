<script lang="ts">
  import { ArrowUpRight } from "@lucide/svelte";
  import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
  } from "$lib/components/ui/card";
  import InstructorPreview from "$lib/components/instructor-preview/instructor-preview.svelte";
  import ContentWrapper from "\$lib/components/content/content-wrapper.svelte";
  import {
    PageHeader,
    PageHeaderDescription,
    PageHeaderHeading,
  } from "$lib/components/page-header";

  let { data } = $props();

  let instructors = $derived(data.instructors);
</script>

<ContentWrapper>
  <PageHeader>
    <PageHeaderHeading>Most Rated Instructors</PageHeaderHeading>
    <PageHeaderDescription class="text-muted-foreground">
      Who has the most ratings on Rate My Professors, regardless of their
      rating? We've got the top 100.
    </PageHeaderDescription>
  </PageHeader>
  <Card>
    <CardContent class="mt-4">
      {#each instructors as instructor, index}
        <InstructorPreview
          {instructor}
          showRating={true}
          showOtherDetails={true}
          rank={index + 1}
        />
      {/each}
    </CardContent>
    <CardHeader>
      <CardDescription class="flex">
        Sourced from
        <a
          class="ml-1 flex items-center font-medium underline-offset-4 hover:underline"
          href="https://www.ratemyprofessors.com/"
          target="_blank"
        >
          Rate My Professors
          <ArrowUpRight class="inline h-4 w-4" />
        </a>
      </CardDescription>
    </CardHeader>
  </Card>
</ContentWrapper>
