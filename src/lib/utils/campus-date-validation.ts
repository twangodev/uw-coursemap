/**
 * Campus date validation utilities for handling available dates with building data
 */

export interface DateIndexEntry {
	total_buildings: number;
	total_instructors: number;
	total_meetings: number;
	total_students: number;
}

export interface DateValidationResult {
	isValid: boolean;
	redirectDate?: string;
	selectedDate: Date;
}

/**
 * Parse and validate date from URL parameter (MM-DD-YY format)
 */
export function parseDateFromParam(dayParam: string | null): Date {
	if (!dayParam) {
		return new Date(); // Default to today
	}

	try {
		// Expect MM-DD-YY format
		const parts = dayParam.split('-');
		if (parts.length !== 3) {
			throw new Error('Invalid date format');
		}

		const [monthStr, dayStr, yearStr] = parts;
		
		// Validate and parse components
		const month = parseInt(monthStr, 10);
		const day = parseInt(dayStr, 10);
		const year = parseInt(yearStr, 10);

		// Basic validation
		if (month < 1 || month > 12 || day < 1 || day > 31 || yearStr.length !== 2) {
			throw new Error('Invalid date values');
		}

		// Convert 2-digit year to 4-digit (assume 20XX for this application)
		const fullYear = 2000 + year;

		// Create date and validate it's a real date
		const date = new Date(fullYear, month - 1, day);
		
		// Check if the date is valid (handles invalid dates like Feb 31)
		if (
			date.getFullYear() !== fullYear ||
			date.getMonth() !== month - 1 ||
			date.getDate() !== day
		) {
			throw new Error('Invalid date');
		}

		return date;
	} catch (err) {
		console.warn('Failed to parse date parameter:', dayParam, err);
		return new Date(); // Fallback to today
	}
}

/**
 * Format date for API and URL parameters (MM-DD-YY format)
 */
export function formatDateForAPI(date: Date): string {
	const month = String(date.getMonth() + 1).padStart(2, '0');
	const day = String(date.getDate()).padStart(2, '0');
	const year = String(date.getFullYear()).slice(-2);
	return `${month}-${day}-${year}`;
}

/**
 * Find nearest valid date from available dates with total_buildings > 0
 */
export function findNearestValidDate(
	targetDate: Date, 
	availableDates: Record<string, DateIndexEntry>
): string | null {
	const validDates = Object.entries(availableDates)
		.filter(([_, data]) => data.total_buildings > 0)
		.map(([dateStr, _]) => dateStr);

	if (validDates.length === 0) {
		return null;
	}

	// Convert target date to timestamp for comparison
	const targetTime = targetDate.getTime();

	// Find the date with minimum time difference
	let nearestDate = validDates[0];
	let minDifference = Infinity;

	for (const dateStr of validDates) {
		try {
			// Parse the date string (MM-DD-YY format)
			const [monthStr, dayStr, yearStr] = dateStr.split('-');
			const month = parseInt(monthStr, 10);
			const day = parseInt(dayStr, 10);
			const year = 2000 + parseInt(yearStr, 10);
			
			const date = new Date(year, month - 1, day);
			const difference = Math.abs(date.getTime() - targetTime);
			
			if (difference < minDifference) {
				minDifference = difference;
				nearestDate = dateStr;
			}
		} catch (err) {
			console.warn('Failed to parse available date:', dateStr, err);
		}
	}

	return nearestDate;
}

/**
 * Fetch available dates from the static API
 */
export async function fetchAvailableDates(
	fetch: typeof globalThis.fetch
): Promise<Record<string, DateIndexEntry>> {
	try {
		const response = await fetch('https://static.uwcourses.com/meetings/index.json');
		if (response.ok) {
			return await response.json();
		} else {
			console.warn('Failed to load available dates index:', response.statusText);
			return {};
		}
	} catch (err) {
		console.warn('Failed to fetch available dates index:', err);
		return {};
	}
}

/**
 * Validate a date parameter against available dates and return validation result
 */
export function validateDateParam(
	dayParam: string | null,
	availableDates: Record<string, DateIndexEntry>
): DateValidationResult {
	// Handle missing day parameter
	if (!dayParam) {
		const today = new Date();
		const todayParam = formatDateForAPI(today);
		
		// Check if today is valid first
		if (availableDates[todayParam]?.total_buildings > 0) {
			return {
				isValid: false,
				redirectDate: todayParam,
				selectedDate: today
			};
		}
		
		// Find nearest valid date to today
		const nearestDate = findNearestValidDate(today, availableDates);
		return {
			isValid: false,
			redirectDate: nearestDate || todayParam,
			selectedDate: today
		};
	}

	// Parse and validate the date parameter
	const selectedDate = parseDateFromParam(dayParam);
	const dateStr = formatDateForAPI(selectedDate);

	// Check for malformed date (parsed date doesn't match parameter)
	if (dateStr !== dayParam) {
		// Check if corrected date is valid
		if (availableDates[dateStr]?.total_buildings > 0) {
			return {
				isValid: false,
				redirectDate: dateStr,
				selectedDate
			};
		}
		
		// Find nearest valid date to corrected date
		const nearestDate = findNearestValidDate(selectedDate, availableDates);
		return {
			isValid: false,
			redirectDate: nearestDate || dateStr,
			selectedDate
		};
	}

	// Check if the requested date is available and has buildings
	if (!availableDates[dayParam] || availableDates[dayParam].total_buildings === 0) {
		// Find nearest valid date
		const nearestDate = findNearestValidDate(selectedDate, availableDates);
		if (nearestDate) {
			return {
				isValid: false,
				redirectDate: nearestDate,
				selectedDate
			};
		}
	}

	// Date is valid or no better alternative found
	return {
		isValid: true,
		selectedDate
	};
}