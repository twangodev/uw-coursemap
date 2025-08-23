<script lang="ts">
  import { Share2 } from '@lucide/svelte';
  import * as Sheet from '$lib/components/ui/sheet';
  import { ScrollArea } from '$lib/components/ui/scroll-area';
  import { Button } from '$lib/components/ui/button';
  import type { Course } from "$lib/types/course.ts";
  import type { CourseMeeting } from '$lib/utils/schedule/types';
  import { courseReferenceToString } from '$lib/types/course';
  import { generateICS, downloadICS } from '$lib/utils/schedule/ics-generator';
  import { 
    groupMeetingsBySection, 
    sortSectionGroups, 
    parseSectionKey, 
    filterMeetingsBySelection 
  } from '$lib/utils/schedule/section-utils';

  interface Props {
    course: Course;
    meetings?: CourseMeeting[];
  }

  let { course, meetings }: Props = $props();
  
  let selectedSections = $state<Set<string>>(new Set());
  
  const sortedGroups = $derived(() => {
    if (!meetings) return [];
    const groups = groupMeetingsBySection(meetings);
    return sortSectionGroups(groups);
  });
  
  function toggleSection(groupKey: string) {
    const newSections = new Set(selectedSections);
    if (newSections.has(groupKey)) {
      newSections.delete(groupKey);
    } else {
      newSections.add(groupKey);
    }
    selectedSections = newSections;
  }
  
  async function handleExport() {
    if (!meetings || selectedSections.size === 0) return;
    
    const meetingsToExport = filterMeetingsBySelection(meetings, selectedSections);
    
    try {
      const courseName = courseReferenceToString(course.course_reference);
      const icsContent = await generateICS(meetingsToExport, courseName);
      const filename = `${courseName.replace(/[^a-z0-9]/gi, '_')}_schedule.ics`;
      downloadICS(icsContent, filename);
    } catch (error) {
      console.error('Failed to export calendar:', error);
    }
  }
</script>

<Sheet.Root>
  <Sheet.Trigger class="text-xs text-muted-foreground flex items-center gap-1 hover:text-foreground transition-colors">
    <Share2 class="h-3 w-3" />
    Export to your calendar
  </Sheet.Trigger>
  <Sheet.Content side="right" class="w-full sm:max-w-md flex flex-col">
    <Sheet.Header>
      <Sheet.Title>Export {courseReferenceToString(course.course_reference)} Schedule</Sheet.Title>
      <Sheet.Description>
        Select which sections you want to export. The file will work with Google Calendar, Apple Calendar, Outlook, and other calendar apps.
      </Sheet.Description>
    </Sheet.Header>
    
    <ScrollArea class="flex-1 my-4 min-h-0">
      <div class="space-y-2 pr-4">
        {#each sortedGroups() as [groupKey, sectionMeetings]}
          {@const { sectionName, instructorName } = parseSectionKey(groupKey)}
          <button
            class="w-full text-left p-3 rounded-md border transition-colors {selectedSections.has(groupKey) ? 'bg-primary/10 border-primary' : 'border-border hover:bg-muted/50'}"
            onclick={() => toggleSection(groupKey)}
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
    </ScrollArea>
    
    <Sheet.Footer>
      <Button variant="outline" onclick={() => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))}>
        Cancel
      </Button>
      <Button 
        onclick={handleExport}
        disabled={selectedSections.size === 0}
      >
        Download Calendar File
      </Button>
    </Sheet.Footer>
  </Sheet.Content>
</Sheet.Root>