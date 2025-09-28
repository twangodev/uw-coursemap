<script lang="ts">
  import { ScheduleXCalendar } from '@schedule-x/svelte';
  import '@schedule-x/theme-shadcn/dist/index.css';
  import type { Course } from "$lib/types/course.ts";
  import type { CourseMeeting } from '$lib/utils/schedule/types';
  import { mode } from 'mode-watcher';
  import { transformMeetingsToScheduleEvents } from '$lib/utils/schedule/meeting-transformer';
  import { createScheduleCalendarConfig } from '$lib/utils/schedule/schedule-config';
  import CourseExportDialog from '../course-export-dialog.svelte';
  import { m } from "$lib/paraglide/messages";

  interface Props {
    course: Course;
    meetings?: CourseMeeting[];
    isVisible?: boolean;
  }

  let { course, meetings, isVisible = false }: Props = $props();
  let calendarApp = $state<any>(null);
  
  // Initialize calendar when tab becomes visible
  $effect(() => {
    if (isVisible && meetings && !calendarApp) {
      const events = transformMeetingsToScheduleEvents(meetings);
      calendarApp = createScheduleCalendarConfig(events, meetings, mode.current);
    }
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
        {m["course.schedule.timezoneInfo"]()}
      </p>
      <CourseExportDialog {course} {meetings} />
    </div>
  {:else if !meetings || meetings.length === 0}
    <div class="flex items-center justify-center h-64">
      <p class="text-muted-foreground">{m["course.schedule.noScheduleInfo"]()}</p>
    </div>
  {:else}
    <div class="flex items-center justify-center h-64">
      <p class="text-muted-foreground">{m["course.schedule.loadingCalendar"]()}</p>
    </div>
  {/if}
</div>

<style>
    :global(.sx-svelte-calendar-wrapper) {
        height: 600px;
    }

</style>