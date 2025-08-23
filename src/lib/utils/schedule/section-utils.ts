import type { CourseMeeting } from './types';

/**
 * Creates a unique key for a meeting based on section name and instructor
 */
export function getSectionKey(meeting: CourseMeeting): string {
  const baseSectionName = meeting.name.split('#')[0].trim();
  const instructorKey = meeting.instructors?.length > 0 
    ? meeting.instructors.join(', ')
    : 'No Instructor';
  return `${baseSectionName}|${instructorKey}`;
}

/**
 * Parses a section key back into section name and instructor
 */
export function parseSectionKey(key: string): { sectionName: string; instructorName: string } {
  const [sectionName, instructorName] = key.split('|');
  return { sectionName, instructorName };
}

/**
 * Groups meetings by section name and instructor
 */
export function groupMeetingsBySection(meetings: CourseMeeting[]): Map<string, CourseMeeting[]> {
  const groups = new Map<string, CourseMeeting[]>();
  
  meetings.forEach(meeting => {
    const groupKey = getSectionKey(meeting);
    
    if (!groups.has(groupKey)) {
      groups.set(groupKey, []);
    }
    groups.get(groupKey)!.push(meeting);
  });
  
  return groups;
}

/**
 * Sorts section groups by their earliest meeting start time
 */
export function sortSectionGroups(groups: Map<string, CourseMeeting[]>): Array<[string, CourseMeeting[]]> {
  return Array.from(groups).sort((a, b) => {
    const aEarliest = Math.min(...a[1].map(m => m.start_time));
    const bEarliest = Math.min(...b[1].map(m => m.start_time));
    return aEarliest - bEarliest;
  });
}

/**
 * Filters meetings based on selected section keys
 */
export function filterMeetingsBySelection(
  meetings: CourseMeeting[],
  selectedSections: Set<string>
): CourseMeeting[] {
  return meetings.filter(meeting => selectedSections.has(getSectionKey(meeting)));
}