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
 * Generate deterministic colors for a calendar based on section key
 * Uses proven HSL values that guarantee WCAG contrast compliance
 */
function getSectionColor(sectionKey: string) {
  // Hash the section key to get a consistent hue
  let hash = 0;
  for (let i = 0; i < sectionKey.length; i++) {
    hash = sectionKey.charCodeAt(i) + ((hash << 5) - hash);
  }
  const hue = Math.abs(hash % 360);
  
  // Use proven HSL values that always have good contrast
  return {
    lightColors: {
      main: `hsl(${hue}, 70%, 50%)`,
      container: `hsl(${hue}, 25%, 95%)`,  // Very light background
      onContainer: `hsl(${hue}, 60%, 25%)`  // Dark text with color
    },
    darkColors: {
      main: `hsl(${hue}, 60%, 60%)`,
      container: `hsl(${hue}, 30%, 15%)`,   // Very dark background
      onContainer: `hsl(${hue}, 40%, 85%)`  // Light text with color
    }
  };
}

/**
 * Create calendar configurations from meetings
 */
function generateCalendars(meetings: CourseMeeting[]) {
  const calendars: Record<string, any> = {};
  const sectionMap = new Map<string, string>();
  
  // Get unique section keys and maintain mapping
  meetings.forEach(meeting => {
    const sectionKey = getSectionKey(meeting);
    const calendarId = sectionKey.toLowerCase().replace(/[^a-z0-9]/g, '');
    if (!sectionMap.has(calendarId)) {
      sectionMap.set(calendarId, sectionKey);
    }
  });
  
  // Create a calendar for each unique section with light/dark theme colors
  sectionMap.forEach((originalKey, calendarId) => {
    const colors = getSectionColor(originalKey);
    calendars[calendarId] = {
      colorName: calendarId,
      lightColors: colors.lightColors,
      darkColors: colors.darkColors
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