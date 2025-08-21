<script lang="ts">
  import { onMount } from 'svelte';
  import { ScheduleXCalendar } from '@schedule-x/svelte';
  import { createCalendar, createViewWeek } from '@schedule-x/calendar';
  import { createCurrentTimePlugin } from '@schedule-x/current-time';
  import '@schedule-x/theme-shadcn/dist/index.css';
  import type { Course } from "$lib/types/course.ts";
  import { mode } from 'mode-watcher';

  interface Props {
    course: Course;
  }

  let { course }: Props = $props();
  
  let calendarApp = $state<any>(null);
  
  onMount(() => {
    calendarApp = createCalendar({
      views: [createViewWeek()],
      defaultView: 'week',
      events: [
        {
          id: '1',
          title: 'Sample Event',
          start: '2024-12-10 09:00',
          end: '2024-12-10 10:00',
        }
      ],
      plugins: [
        createCurrentTimePlugin()
      ],
      theme: 'shadcn',
      locale: 'en-US',
      firstDayOfWeek: 0, // Sunday
      dayBoundaries: {
        start: '07:00',
        end: '22:00'
      },
      weekOptions: {
        gridHeight: 400,
        nDays: 7
      }
    });
    
    // Set initial theme
    calendarApp.setTheme(mode.current === 'dark' ? 'dark' : 'light');
  });
  
  // Watch for theme changes
  $effect(() => {
    if (calendarApp) {
      calendarApp.setTheme(mode.current === 'dark' ? 'dark' : 'light');
    }
  });
</script>

<div class="calendar-container">
  {#if calendarApp}
    <ScheduleXCalendar {calendarApp} />
  {:else}
    <div class="flex items-center justify-center h-full">
      <p class="text-muted-foreground">Loading calendar...</p>
    </div>
  {/if}
</div>

<style>
  .calendar-container {
    height: 600px;
    width: 100%;
  }
  
</style>