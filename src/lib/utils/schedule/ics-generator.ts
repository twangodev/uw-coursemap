import type { CourseMeeting } from './types';
import { createEvents, type EventAttributes } from 'ics';

/**
 * Convert timestamp to ICS date array [year, month, day, hour, minute]
 */
function timestampToDateArray(timestamp: number): [number, number, number, number, number] {
  const date = new Date(timestamp);
  return [
    date.getFullYear(),
    date.getMonth() + 1, // ICS uses 1-12 for months
    date.getDate(),
    date.getHours(),
    date.getMinutes()
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
 */
export async function generateICS(
  meetings: CourseMeeting[],
  courseName: string
): Promise<string> {
  // Convert meetings to ICS events
  const events: EventAttributes[] = meetings.map((meeting, index) => {
    const startArray = timestampToDateArray(meeting.start_time);
    const duration = getDurationInMinutes(meeting.start_time, meeting.end_time);
    
    const location = meeting.location
      ? `${meeting.location.building}${meeting.location.room ? ' ' + meeting.location.room : ''}`
      : undefined;

    // Build description
    const descriptionParts: string[] = [];
    descriptionParts.push(`Type: ${meeting.type}`);
    
    if (meeting.instructors && meeting.instructors.length > 0) {
      descriptionParts.push(`Instructor(s): ${meeting.instructors.join(', ')}`);
    }
    
    if (meeting.current_enrollment) {
      descriptionParts.push(`Enrollment: ${meeting.current_enrollment}`);
    }

    const courseStr = `${meeting.course_reference.subjects.join('/')} ${meeting.course_reference.course_number}`;
    descriptionParts.push(`Course: ${courseStr}`);

    return {
      title: meeting.name,
      start: startArray,
      duration: { minutes: duration },
      location: location,
      description: descriptionParts.join('\n'),
      categories: [meeting.type],
      productId: 'uwcourses.com',
      calName: courseName,
      uid: `${courseStr.replace(/\//g, '')}-${meeting.start_time}-${index}@uwcourses.com`
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