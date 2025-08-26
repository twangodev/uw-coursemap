import {
    createCalendar,
    createViewDay,
    createViewWeek,
    createViewMonthGrid,
    createViewMonthAgenda,
    viewWeek
} from '@schedule-x/calendar';
import { createCalendarControlsPlugin } from '@schedule-x/calendar-controls';
import { createCurrentTimePlugin } from '@schedule-x/current-time';
import { createEventModalPlugin } from '@schedule-x/event-modal';
import type { ScheduleEvent } from './types';
import { calculateDayBoundaries } from './schedule-boundaries';
import { getMadisonTimeOffset } from './timezone-utils';
import { getSectionKey } from './section-utils';
import type { CourseMeeting } from './types';

/**
 * Generate a random color for a calendar
 */
function getRandomColor() {
  const hue = Math.floor(Math.random() * 360);
  const main = `hsl(${hue}, 70%, 50%)`;
  const container = `hsl(${hue}, 70%, 90%)`;
  const onContainer = `hsl(${hue}, 70%, 20%)`;
  return { main, container, onContainer };
}

/**
 * Create calendar configurations from meetings
 */
function generateCalendars(meetings: CourseMeeting[]) {
  const calendars: Record<string, any> = {};
  const sections = new Set<string>();
  
  // Get unique section keys
  meetings.forEach(meeting => {
    const sectionKey = getSectionKey(meeting);
    const calendarId = sectionKey.toLowerCase().replace(/[^a-z0-9]/g, '');
    sections.add(calendarId);
  });
  
  // Create a calendar for each unique section
  sections.forEach(calendarId => {
    const colors = getRandomColor();
    calendars[calendarId] = {
      colorName: calendarId,
      lightColors: colors
    };
  });
  
  return calendars;
}

/**
 * Create a configured Schedule-X calendar instance
 * 
 * @param events Array of schedule events to display
 * @param meetings Array of course meetings (for extracting sections)
 * @param currentTheme Current theme mode ('light' or 'dark')
 * @returns Configured calendar instance
 */
export function createScheduleCalendarConfig(
  events: ScheduleEvent[],
  meetings: CourseMeeting[],
  currentTheme: 'light' | 'dark' | 'system' = 'light'
) {
  const dayBoundaries = calculateDayBoundaries(events);
  const calendars = generateCalendars(meetings);
  
  const calendarApp = createCalendar(
    {
      views: [
          createViewMonthGrid(),
          createViewWeek(),
          createViewDay(),
        createViewMonthAgenda()
      ],
      defaultView: viewWeek.name,
      events: events,
      calendars: calendars,
      theme: 'shadcn',
      locale: 'en-US',
      firstDayOfWeek: 0,
      weekOptions: {
        gridHeight: 1000,
        eventWidth: 95,
        nDays: 7
      },
      monthGridOptions: {
        nEventsPerDay: 3
      },
      dayBoundaries: dayBoundaries
    },
    [
      createEventModalPlugin(),
      createCalendarControlsPlugin(),
      createCurrentTimePlugin({
        timeZoneOffset: getMadisonTimeOffset()
      })
    ]
  );
  
  calendarApp.setTheme(currentTheme === 'dark' ? 'dark' : 'light');
  
  return calendarApp;
}