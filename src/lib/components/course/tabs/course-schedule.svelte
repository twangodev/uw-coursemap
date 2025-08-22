<script lang="ts">
  import { onMount } from 'svelte';
  import { ScheduleXCalendar } from '@schedule-x/svelte';
  import '@schedule-x/theme-shadcn/dist/index.css';
  import type { Course } from "$lib/types/course.ts";
  import type { CourseMeeting } from '$lib/utils/schedule/types';
  import { mode } from 'mode-watcher';
  import { transformMeetingsToScheduleEvents } from '$lib/utils/schedule/meeting-transformer';
  import { createScheduleCalendarConfig } from '$lib/utils/schedule/schedule-config';
  import { CALENDAR_CONFIG, FEATURE_FLAGS } from '$lib/utils/schedule/schedule-constants';

  interface Props {
    course: Course;
    meetings?: CourseMeeting[];
  }

  let { course, meetings }: Props = $props();
  
  let calendarApp = $state<any>(null);
  
  onMount(() => {
    const events = transformMeetingsToScheduleEvents(meetings);
    calendarApp = createScheduleCalendarConfig(events, mode.current);
  });
  
  // Watch for theme changes
  $effect(() => {
    if (calendarApp && FEATURE_FLAGS.enableThemeSync) {
      calendarApp.setTheme(mode.current === 'dark' ? 'dark' : 'light');
    }
  });
</script>

<div class="w-full" style="--calendar-height: {CALENDAR_CONFIG.containerHeight}px">
  {#if calendarApp}
    <ScheduleXCalendar {calendarApp}/>
    <p class="text-xs text-muted-foreground mt-2">
      All times shown in America/Chicago timezone.
    </p>
  {:else}
    <div class="flex items-center justify-center h-full">
      <p class="text-muted-foreground">Loading calendar...</p>
    </div>
  {/if}
</div>

<style>
    :global(.sx-svelte-calendar-wrapper) {
        height: var(--calendar-height, 600px);
    }
</style>