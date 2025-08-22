import type { ScheduleEvent, DayBoundaries } from './types';

export const DEFAULT_DAY_BOUNDARIES: DayBoundaries = {
  start: '00:00',
  end: '24:00'
};

/**
 * Calculate optimal day boundaries based on event times
 * Finds the earliest start time and latest end time, with appropriate buffers
 * 
 * @param events Array of schedule events
 * @returns Day boundaries with start and end times
 */
export function calculateDayBoundaries(events: ScheduleEvent[]): DayBoundaries {
  if (events.length === 0) {
    return DEFAULT_DAY_BOUNDARIES;
  }
  
  // Find earliest and latest times across all events
  let earliestTime = '24:00';
  let latestTime = '00:00';
  
  events.forEach(event => {
    const startTime = event.start.split(' ')[1]; // Get time part (HH:MM)
    const endTime = event.end.split(' ')[1];
    
    if (startTime < earliestTime) earliestTime = startTime;
    if (endTime > latestTime) latestTime = endTime;
  });
  
  // Parse hours and minutes
  const earliestHour = parseInt(earliestTime.split(':')[0]);
  const latestHour = parseInt(latestTime.split(':')[0]);
  const latestMinutes = parseInt(latestTime.split(':')[1]);
  
  // Floor the start hour (e.g., 7:55 -> 7:00)
  const boundaryStart = earliestHour;
  
  // Ceiling the end hour + 1 buffer (e.g., 5:30 PM -> 7:00 PM)
  const boundaryEnd = Math.min(24, latestMinutes > 0 ? latestHour + 2 : latestHour + 1);
  
  return {
    start: `${String(boundaryStart).padStart(2, '0')}:00`,
    end: `${String(boundaryEnd).padStart(2, '0')}:00`
  };
}

/**
 * Calculate day boundaries for events within a specific date range
 */
export function calculateDayBoundariesForRange(
  events: ScheduleEvent[],
  startDate: string,
  endDate: string
): DayBoundaries {
  // Filter events within the date range
  const eventsInRange = events.filter(event => {
    const eventDate = event.start.split(' ')[0];
    return eventDate >= startDate && eventDate <= endDate;
  });
  
  // If no events in this range, use sensible defaults
  if (eventsInRange.length === 0) {
    return {
      start: '08:00',
      end: '18:00'
    };
  }
  
  return calculateDayBoundaries(eventsInRange);
}