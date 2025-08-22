import { formatInTimeZone } from 'date-fns-tz';
import { MADISON_TIMEZONE } from './types';

/**
 * Calculate the timezone offset between user's local time and Madison time
 * This is used to make the current time indicator show Madison's current time
 * 
 * @returns Offset in minutes to add to local time to get Madison time
 */
export function getMadisonTimeOffset(): number {
  const now = new Date();
  const madisonTime = new Date(
    formatInTimeZone(now, MADISON_TIMEZONE, "yyyy-MM-dd'T'HH:mm:ss")
  );
  
  // Calculate difference in minutes
  return Math.round((madisonTime.getTime() - now.getTime()) / 60000);
}