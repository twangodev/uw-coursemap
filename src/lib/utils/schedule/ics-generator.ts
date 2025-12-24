import type { CourseMeeting } from './types';
import { createEvents, type EventAttributes } from 'ics';
import { CourseUtils } from '$lib/types/course';

/**
 * Convert timestamp to UTC date array [year, month, day, hour, minute]
 * The timestamp is already in milliseconds and represents the actual time in Chicago
 * We need to get the UTC components for the ICS file
 */
function timestampToUTCDateArray(timestamp: number): [number, number, number, number, number] {
  const date = new Date(timestamp);
  return [
    date.getUTCFullYear(),
    date.getUTCMonth() + 1, // ICS uses 1-12 for months
    date.getUTCDate(),
    date.getUTCHours(),
    date.getUTCMinutes()
  ];
}

/**
 * Calculate duration in minutes between two timestamps
 */
function getDurationInMinutes(startTime: number, endTime: number): number {
  return Math.round((endTime - startTime) / 60000);
}

/**
 * Generate ICS file content for selected meetings
 * 
 * Note: Meeting timestamps are stored as Unix timestamps that represent the actual
 * time in America/Chicago timezone. We convert these to UTC for the ICS file,
 * which ensures the events appear at the correct local time regardless of the
 * viewer's timezone or DST changes.
 */
export async function generateICS(
  meetings: CourseMeeting[],
  courseName: string
): Promise<string> {
  // Convert meetings to ICS events with UTC times
  const events: EventAttributes[] = meetings.map((meeting, index) => {
    const startArray = timestampToUTCDateArray(meeting.start_time);
    const duration = getDurationInMinutes(meeting.start_time, meeting.end_time);
    
    const location = meeting.location
      ? `${meeting.location.building}${meeting.location.room ? ' ' + meeting.location.room : ''}`
      : undefined;

    // Build description with useful persistent information
    const descriptionParts: string[] = [];
    
    // Extract section info from meeting name (e.g., "LEC 001 #12345" -> "LEC 001")
    const sectionName = meeting.name.split('#')[0].trim();
    
    if (meeting.instructors && meeting.instructors.length > 0) {
      descriptionParts.push(`Instructor(s): ${meeting.instructors.join(', ')}`);
    }

    // Use course code + section as the title for better calendar visibility
    const courseStr = CourseUtils.courseReferenceToString(meeting.course_reference);
    const eventTitle = `${courseStr} ${sectionName}`;

    return {
      title: eventTitle,
      start: startArray,
      startInputType: 'utc' as const,
      startOutputType: 'utc' as const,
      duration: { minutes: duration },
      location: location,
      description: descriptionParts.join('\n'),
      categories: [meeting.type],
      productId: 'uwcourses.com',
      calName: courseName,
      uid: `${courseStr.replace(/[\s\/]/g, '')}-${meeting.start_time}-${index}@uwcourses.com`
    };
  });

  // Generate ICS string
  const { error, value } = createEvents(events);
  
  if (error) {
    throw new Error(`Failed to generate ICS: ${error.message}`);
  }
  
  return value || '';
}

/**
 * Download ICS file to user's computer
 */
export function downloadICS(content: string, filename: string) {
  const blob = new Blob([content], { type: 'text/calendar;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}