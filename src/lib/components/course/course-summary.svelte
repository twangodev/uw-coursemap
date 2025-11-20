<script lang="ts">
  import { Sparkles } from "@lucide/svelte";
  import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
  } from "$lib/components/ui/card/index.js";
  import type { Course } from "$lib/types/course.ts";
  import type { FullInstructorInformation } from "$lib/types/instructor.ts";

  interface Props {
    course: Course;
    instructors: FullInstructorInformation[];
  }

  let { course, instructors }: Props = $props();

  let summary = $state('');
  let loading = $state(false);
  let error = $state<string | null>(null);

  async function generateSummary() {
    loading = true;
    error = null;
    summary = '';

    try {
      // Format instructor data for the API
      const instructorStats = instructors.map(instructor => ({
        name: instructor.name,
        rating: instructor.rmp_data?.average_rating,
        difficulty: instructor.rmp_data?.average_difficulty,
        wouldTakeAgain: instructor.rmp_data?.would_take_again_percent,
        numRatings: instructor.rmp_data?.num_ratings,
      })).filter(i => i.rating !== undefined);

      const response = await fetch('/api/summarize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          courseTitle: course.course_title,
          courseDescription: course.description,
          courseNumber: course.course_reference.course_number,
          subject: course.course_reference.subjects[0],
          instructors: instructorStats,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate summary');
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body');
      }

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') {
              loading = false;
              return;
            }
            try {
              const parsed = JSON.parse(data);
              if (parsed.text) {
                summary += parsed.text;
              }
            } catch (e) {
              // Skip invalid JSON
            }
          }
        }
      }

      loading = false;
    } catch (err) {
      error = err instanceof Error ? err.message : 'An error occurred';
      console.error('Error generating summary:', err);
      loading = false;
    }
  }

  // Auto-generate summary when component mounts
  $effect(() => {
    generateSummary();
  });
</script>

<div class="rainbow-border-wrapper">
  <Card>
    <CardHeader
      class="flex flex-row items-center justify-between space-y-0 pb-2"
    >
      <CardTitle class="text-base font-medium">AI Summary</CardTitle>
      <Sparkles class="text-muted-foreground h-4 w-4" />
    </CardHeader>
    <CardContent>
      {#if loading && !summary}
        <div class="flex items-center gap-2 py-2">
          <Sparkles class="h-4 w-4 animate-pulse text-muted-foreground" />
          <span class="text-sm text-muted-foreground">Generating summary...</span>
        </div>
      {:else if summary}
        <div class="space-y-3">
          <p class="text-sm break-words">
            {summary}{#if loading}<span class="animate-pulse">▊</span>{/if}
          </p>
          <div class="flex items-center justify-end gap-1.5 pt-1">
            <span class="text-xs text-muted-foreground">Powered by</span>
            <a
              href="https://claude.ai"
              target="_blank"
              rel="noopener noreferrer"
              class="claude-link text-xs font-medium hover:underline flex items-center gap-1"
            >
              Claude
              <Sparkles class="h-3 w-3" />
            </a>
          </div>
        </div>
      {:else if error}
        <div class="rounded-md bg-destructive/10 p-3">
          <p class="text-sm text-destructive">{error}</p>
        </div>
      {/if}
    </CardContent>
  </Card>
</div>

<style>
  .rainbow-border-wrapper {
    position: relative;
    border-radius: 0.5rem;
    padding: 2px;
    background: linear-gradient(
      90deg,
      rgba(59, 130, 246, 0.6),
      rgba(139, 92, 246, 0.6),
      rgba(167, 139, 250, 0.6),
      rgba(52, 211, 153, 0.6),
      rgba(59, 130, 246, 0.6)
    );
    background-size: 300% 300%;
    animation: shimmer 3s linear infinite;
  }

  .rainbow-border-wrapper :global(.card) {
    border: none;
  }

  .claude-link {
    color: #CC785C;
    transition: opacity 0.2s ease;
  }

  .claude-link:hover {
    opacity: 0.8;
  }

  @keyframes shimmer {
    0% {
      background-position: 0% 50%;
    }
    100% {
      background-position: 300% 50%;
    }
  }
</style>
