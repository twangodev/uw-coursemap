// Type definitions for schedule-related data structures

export interface MeetingLocation {
  building: string;
  room: string | null;
  capacity?: number;
  coordinates?: [number | null, number | null];
}

export interface CourseMeeting {
  course_reference: {
    course_number: number;
    subjects: string[];
  };
  current_enrollment: number;
  start_time: number; // Unix timestamp in milliseconds
  end_time: number;   // Unix timestamp in milliseconds
  instructors: string[];
  location: MeetingLocation | null;
  name: string;
  type: 'CLASS' | 'DISCUSSION' | 'LAB' | 'EXAM' | 'SEMINAR';
}

export interface ScheduleEvent {
  id: string;
  title: string;
  start: string; // Format: 'YYYY-MM-DD HH:MM'
  end: string;   // Format: 'YYYY-MM-DD HH:MM'
  calendarId: string; // References a calendar for color
  // Store additional metadata in a way that's compatible with Schedule-X
  // but also allows us to access our custom data
  people?: string[]; // instructors
  location?: string; // building and room
  description?: string; // can store JSON stringified metadata
  _customContent?: {
    timeGrid?: string;
    monthGrid?: string;
  };
}

export interface DayBoundaries {
  start: string; // Format: 'HH:MM'
  end: string;   // Format: 'HH:MM'
}

export const MADISON_TIMEZONE = 'America/Chicago';