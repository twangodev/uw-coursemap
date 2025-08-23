<script lang="ts">
  import { onMount } from 'svelte';
  import { ScheduleXCalendar } from '@schedule-x/svelte';
  import '@schedule-x/theme-shadcn/dist/index.css';
  import type { Course } from "$lib/types/course.ts";
  import type { CourseMeeting } from '$lib/utils/schedule/types';
  import { mode } from 'mode-watcher';
  import { transformMeetingsToScheduleEvents } from '$lib/utils/schedule/meeting-transformer';
  import { createScheduleCalendarConfig } from '$lib/utils/schedule/schedule-config';
  import CourseExportDialog from '../course-export-dialog.svelte';

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
    if (calendarApp) {
      calendarApp.setTheme(mode.current === 'dark' ? 'dark' : 'light');
    }
  });
</script>

<div class="w-full">
  {#if calendarApp}
    <ScheduleXCalendar {calendarApp}/>
    <div class="flex justify-between items-center mt-2">
      <p class="text-xs text-muted-foreground">
        All times shown in America/Chicago timezone.
      </p>
      <CourseExportDialog {course} {meetings} />
    </div>
  {:else}
    <div class="flex items-center justify-center h-full">
      <p class="text-muted-foreground">Loading calendar...</p>
    </div>
  {/if}
</div>

<style>
    :global(.sx-svelte-calendar-wrapper) {
        height: 600px;
    }

</style>