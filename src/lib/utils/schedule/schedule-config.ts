import { createCalendar, createViewDay, createViewWeek, createViewMonthGrid, createViewMonthAgenda } from '@schedule-x/calendar';
import { createCalendarControlsPlugin } from '@schedule-x/calendar-controls';
import { createCurrentTimePlugin } from '@schedule-x/current-time';
import { createEventModalPlugin } from '@schedule-x/event-modal';
import type { ScheduleEvent } from './types';
import { calculateDayBoundaries } from './schedule-boundaries';
import { getMadisonTimeOffset } from './timezone-utils';
import { CALENDAR_CONFIG, FEATURE_FLAGS } from './schedule-constants';

// Default calendar configuration options
export const DEFAULT_CALENDAR_OPTIONS = {
  theme: CALENDAR_CONFIG.theme,
  locale: CALENDAR_CONFIG.locale,
  firstDayOfWeek: CALENDAR_CONFIG.weekOptions.firstDayOfWeek,
  weekOptions: {
    gridHeight: CALENDAR_CONFIG.weekOptions.gridHeight,
    eventWidth: CALENDAR_CONFIG.weekOptions.eventWidth,
    nDays: CALENDAR_CONFIG.weekOptions.nDays
  },
  monthGridOptions: {
    nEventsPerDay: CALENDAR_CONFIG.monthGridOptions.nEventsPerDay
  }
};

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
  const dayBoundaries = FEATURE_FLAGS.enableDynamicDayBoundaries 
    ? calculateDayBoundaries(events)
    : null;
  
  // Build views array - always include at least one view
  const views = FEATURE_FLAGS.enableMonthAgendaView 
    ? [
        createViewDay(),
        createViewWeek(),
        createViewMonthGrid(),
        createViewMonthAgenda() // For small screens
      ]
    : [
        createViewDay(),
        createViewWeek(),
        createViewMonthGrid()
      ];
  
  // Build plugins array conditionally based on feature flags
  const plugins = [];
  
  if (FEATURE_FLAGS.enableEventModal) {
    plugins.push(createEventModalPlugin());
  }
  
  if (FEATURE_FLAGS.enableCalendarControls) {
    plugins.push(createCalendarControlsPlugin());
  }
  
  if (FEATURE_FLAGS.enableCurrentTimeIndicator) {
    plugins.push(createCurrentTimePlugin({
      timeZoneOffset: getMadisonTimeOffset()
    }));
  }
  
  const calendarApp = createCalendar(
    {
      views: views as any, // TypeScript needs a non-empty tuple but we guarantee this
      defaultView: CALENDAR_CONFIG.defaultView,
      events: events,
      ...DEFAULT_CALENDAR_OPTIONS,
      ...(dayBoundaries && { dayBoundaries })
    },
    plugins
  );
  
  // Set initial theme if theme sync is enabled
  if (FEATURE_FLAGS.enableThemeSync) {
    calendarApp.setTheme(currentTheme === 'dark' ? 'dark' : 'light');
  }
  
  return calendarApp;
}