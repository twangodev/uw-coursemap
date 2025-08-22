import { formatInTimeZone } from 'date-fns-tz';
import type { CourseMeeting, ScheduleEvent } from './types';
import { MADISON_TIMEZONE } from './types';

// Color mapping for different meeting types
const MEETING_TYPE_COLORS: Record<string, string> = {
  CLASS: '#3b82f6',      // blue
  DISCUSSION: '#10b981',  // green
  LAB: '#f59e0b',        // amber
  EXAM: '#ef4444',       // red
  SEMINAR: '#8b5cf6',    // purple
  DEFAULT: '#6b7280'     // gray
};

/**
 * Format a timestamp in Madison timezone
 * Ensures classes stay at their scheduled time regardless of DST
 */
export function formatMadisonTime(timestamp: number): string {
  return formatInTimeZone(
    new Date(timestamp),
    MADISON_TIMEZONE,
    'yyyy-MM-dd HH:mm'
  );
}

/**
 * Build event title - just the name
 */
export function buildEventTitle(meeting: CourseMeeting): string {
  return meeting.name;
}

/**
 * Transform meetings data from API to Schedule-X event format
 */
export function transformMeetingsToScheduleEvents(
  meetings: CourseMeeting[] | null | undefined
): ScheduleEvent[] {
  if (!meetings || !Array.isArray(meetings)) {
    return [];
  }
  
  return meetings.map((meeting, index) => ({
    id: `meeting-${index}`,
    title: buildEventTitle(meeting),
    start: formatMadisonTime(meeting.start_time),
    end: formatMadisonTime(meeting.end_time),
    color: MEETING_TYPE_COLORS[meeting.type] || MEETING_TYPE_COLORS.DEFAULT,
    people: meeting.instructors,
    location: meeting.location ? 
      `${meeting.location.building}${meeting.location.room ? ' ' + meeting.location.room : ''}` : 
      undefined,
    description: JSON.stringify({
      type: meeting.type,
      enrollment: meeting.current_enrollment,
    }),
  }));
}