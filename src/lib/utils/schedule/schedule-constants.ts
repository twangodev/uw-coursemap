/**
 * Configuration constants for the course schedule feature
 */

// Meeting type color palette
export const MEETING_TYPE_COLORS = {
  CLASS: '#3b82f6',      // blue-500
  DISCUSSION: '#10b981',  // emerald-500
  LAB: '#f59e0b',        // amber-500
  EXAM: '#ef4444',       // red-500
  SEMINAR: '#8b5cf6',    // purple-500
  DEFAULT: '#6b7280'     // gray-500
} as const;

// Calendar view configuration
export const CALENDAR_CONFIG = {
  // Theme and locale
  theme: 'shadcn',
  locale: 'en-US',
  
  // Week view settings
  weekOptions: {
    gridHeight: 1000,      // Total height of time grid in pixels
    eventWidth: 95,        // Width percentage of events
    nDays: 7,             // Number of days to show
    firstDayOfWeek: 0     // 0 = Sunday, 1 = Monday
  },
  
  // Month view settings
  monthGridOptions: {
    nEventsPerDay: 3      // Max events to show per day in month view
  },
  
  // Default view on load
  defaultView: 'week' as const,
  
  // Component dimensions
  containerHeight: 600,    // Calendar container height in pixels
  minContainerWidth: 750,  // Minimum width for large screen features
} as const;

// Timezone configuration
export const TIMEZONE_CONFIG = {
  madison: 'America/Chicago',
  displayFormat: 'yyyy-MM-dd HH:mm',
  timeFormat: 'HH:mm'
} as const;

// Day boundary defaults
export const DAY_BOUNDARY_DEFAULTS = {
  fullDay: {
    start: '00:00',
    end: '24:00'
  },
  business: {
    start: '08:00',
    end: '18:00'
  },
  // Buffer hours for calculated boundaries
  startBuffer: 0,  // Hours to subtract from earliest event
  endBuffer: 1     // Hours to add after latest event
} as const;

// Event display configuration
export const EVENT_DISPLAY = {
  titleMaxLength: 50,
  locationMaxLength: 30,
  showInstructors: true,
  showEnrollment: true,
  showLocation: true
} as const;

// Feature flags for optional functionality
export const FEATURE_FLAGS = {
  enableEventModal: true,
  enableCalendarControls: true,
  enableCurrentTimeIndicator: true,
  enableMonthAgendaView: true,
  enableDynamicDayBoundaries: true,
  enableThemeSync: true
} as const;

// Error messages
export const ERROR_MESSAGES = {
  loadFailed: 'Failed to load course schedule',
  noMeetings: 'No scheduled meetings for this course',
  invalidData: 'Invalid meeting data format',
  calendarInitFailed: 'Failed to initialize calendar'
} as const;