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

/**
 * Create a configured Schedule-X calendar instance
 * 
 * @param events Array of schedule events to display
 * @param currentTheme Current theme mode ('light' or 'dark')
 * @returns Configured calendar instance
 */
export function createScheduleCalendarConfig(
  events: ScheduleEvent[],
  currentTheme: 'light' | 'dark' | 'system' = 'light'
) {
  const dayBoundaries = calculateDayBoundaries(events);
  
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