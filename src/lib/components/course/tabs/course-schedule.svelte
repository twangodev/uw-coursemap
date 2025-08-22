<script lang="ts">
  import { onMount } from 'svelte';
  import { ScheduleXCalendar } from '@schedule-x/svelte';
  import '@schedule-x/theme-shadcn/dist/index.css';
  import type { Course } from "$lib/types/course.ts";
  import type { CourseMeeting } from '$lib/utils/schedule/types';
  import { mode } from 'mode-watcher';
  import { transformMeetingsToScheduleEvents } from '$lib/utils/schedule/meeting-transformer';
  import { createScheduleCalendarConfig } from '$lib/utils/schedule/schedule-config';
  import { Share2 } from '@lucide/svelte';
  import {
    AlertDialog,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogHeader,
    AlertDialogTitle,
    AlertDialogTrigger,
    AlertDialogFooter,
    AlertDialogAction,
    AlertDialogCancel
  } from '$lib/components/ui/alert-dialog';
  import { Button } from '$lib/components/ui/button';
  import { courseReferenceToString } from '$lib/types/course';
  import { generateICS, downloadICS } from '$lib/utils/schedule/ics-generator';

  interface Props {
    course: Course;
    meetings?: CourseMeeting[];
  }

  let { course, meetings }: Props = $props();
  
  let calendarApp = $state<any>(null);
  let selectedSections = $state<Set<string>>(new Set());
  
  // Group meetings by section name AND instructor
  const sectionGroups = $derived(() => {
    if (!meetings) return new Map();
    
    const groups = new Map<string, CourseMeeting[]>();
    meetings.forEach(meeting => {
      // Extract section name without instance number (e.g., "LEC 001 #1" -> "LEC 001")
      const baseSectionName = meeting.name.split('#')[0].trim();
      
      // Create a unique key combining section and instructor(s)
      // If no instructors, just use section name
      const instructorKey = meeting.instructors?.length > 0 
        ? meeting.instructors.join(', ')
        : 'No Instructor';
      const groupKey = `${baseSectionName}|${instructorKey}`;
      
      if (!groups.has(groupKey)) {
        groups.set(groupKey, []);
      }
      groups.get(groupKey)!.push(meeting);
    });
    return groups;
  });
  
  onMount(() => {
    const events = transformMeetingsToScheduleEvents(meetings);
    calendarApp = createScheduleCalendarConfig(events, mode.current);
    
    // Select all sections by default
    if (meetings) {
      const sections = new Set(meetings.map(m => {
        const baseSectionName = m.name.split('#')[0].trim();
        const instructorKey = m.instructors?.length > 0 
          ? m.instructors.join(', ')
          : 'No Instructor';
        return `${baseSectionName}|${instructorKey}`;
      }));
      selectedSections = sections;
    }
  });
  
  async function handleExportToGoogle() {
    if (!meetings || selectedSections.size === 0) return;
    
    // Filter meetings based on selected sections (now includes instructor)
    const meetingsToExport = meetings.filter(meeting => {
      const baseSectionName = meeting.name.split('#')[0].trim();
      const instructorKey = meeting.instructors?.length > 0 
        ? meeting.instructors.join(', ')
        : 'No Instructor';
      const groupKey = `${baseSectionName}|${instructorKey}`;
      return selectedSections.has(groupKey);
    });
    
    try {
      // Generate ICS content
      const courseName = courseReferenceToString(course.course_reference);
      const icsContent = await generateICS(meetingsToExport, courseName);
      
      // Download the file
      const filename = `${courseName.replace(/[^a-z0-9]/gi, '_')}_schedule.ics`;
      downloadICS(icsContent, filename);
    } catch (error) {
      console.error('Failed to export calendar:', error);
      // Could add a toast notification here
    }
  }
  
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
      <AlertDialog>
        <AlertDialogTrigger class="text-xs text-muted-foreground flex items-center gap-1 hover:text-foreground transition-colors">
          <Share2 class="h-3 w-3" />
          Export to your calendar
        </AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Export {courseReferenceToString(course.course_reference)} Schedule</AlertDialogTitle>
            <AlertDialogDescription>
              Select which sections you want to export. The file will work with Google Calendar, Apple Calendar, Outlook, and other calendar apps.
            </AlertDialogDescription>
          </AlertDialogHeader>
          
          <div class="space-y-2 py-4">
            {#each Array.from(sectionGroups()).sort((a, b) => {
              // Sort by the earliest meeting start time in each group
              const aEarliest = Math.min(...a[1].map(m => m.start_time));
              const bEarliest = Math.min(...b[1].map(m => m.start_time));
              return aEarliest - bEarliest;
            }) as [groupKey, sectionMeetings]}
              {@const [sectionName, instructorName] = groupKey.split('|')}
              <button
                class="w-full text-left p-3 rounded-md border transition-colors {selectedSections.has(groupKey) ? 'bg-primary/10 border-primary' : 'border-border hover:bg-muted/50'}"
                onclick={() => {
                  if (selectedSections.has(groupKey)) {
                    const newSections = new Set(selectedSections);
                    newSections.delete(groupKey);
                    selectedSections = newSections;
                  } else {
                    selectedSections = new Set([...selectedSections, groupKey]);
                  }
                }}
              >
                <div class="flex items-start gap-2">
                  <div class="mt-0.5">
                    {#if selectedSections.has(groupKey)}
                      <div class="w-4 h-4 rounded-sm bg-primary flex items-center justify-center">
                        <svg class="w-3 h-3 text-primary-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                        </svg>
                  </div>
                    {:else}
                      <div class="w-4 h-4 rounded-sm border-2 border-input"></div>
                    {/if}
                  </div>
                  <div class="flex-1">
                    <div>
                      <span class="font-medium">{sectionName}</span>
                      <span class="text-muted-foreground ml-2 text-sm">
                        ({sectionMeetings.length} meetings)
                      </span>
                    </div>
                    {#if instructorName && instructorName !== 'No Instructor'}
                      <div class="text-xs text-muted-foreground mt-0.5">
                        {instructorName}
                      </div>
                    {/if}
                  </div>
                </div>
              </button>
            {/each}
          </div>
          
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction 
              onclick={handleExportToGoogle}
              disabled={selectedSections.size === 0}
            >
              Download Calendar File (.ics)
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
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