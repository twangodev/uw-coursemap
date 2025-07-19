import { env } from '$env/dynamic/public';
import { error, redirect } from '@sveltejs/kit';

// Parse and validate date from URL parameter
function parseDateFromParam(dayParam: string | null): Date {
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

// Format date for API (MM-DD-YY)
function formatDateForAPI(date: Date): string {
	const month = String(date.getMonth() + 1).padStart(2, '0');
	const day = String(date.getDate()).padStart(2, '0');
	const year = String(date.getFullYear()).slice(-2);
	return `${month}-${day}-${year}`;
}

export const load = async ({ fetch, url }) => {
	// Check if day parameter exists
	const dayParam = url.searchParams.get('day');
	
	// If no day parameter, redirect to today's date
	if (!dayParam) {
		const todayParam = formatDateForAPI(new Date());
		throw redirect(302, `/campus?day=${todayParam}`);
	}

	// Parse and validate the date parameter
	const selectedDate = parseDateFromParam(dayParam);
	const dateStr = formatDateForAPI(selectedDate);

	// If parsed date doesn't match the parameter (invalid date), redirect to corrected date
	if (dateStr !== dayParam) {
		throw redirect(302, `/campus?day=${dateStr}`);
	}

	try {
		// Load trips data and selected date's highlights data in parallel
		const [tripsResponse, highlightsResponse] = await Promise.all([
			fetch(`${env.PUBLIC_API_URL}/trips.json`),
			fetch(`https://static.uwcourses.com/meetings/${dateStr}.geojson`)
		]);

		// Handle trips data
		let tripsData = null;
		if (tripsResponse.ok) {
			tripsData = await tripsResponse.json();
		} else {
			console.warn('Failed to load trips data:', tripsResponse.statusText);
		}

		// Handle highlights data
		let highlightsData = null;
		if (highlightsResponse.ok) {
			highlightsData = await highlightsResponse.json();
		} else {
			console.warn(`Failed to load highlights data for ${dateStr}:`, highlightsResponse.statusText);
		}

		return {
			subtitle: 'Campus Map',
			description: 'Interactive campus map showing building occupancy and student movement patterns',
			tripsData,
			highlightsData,
			selectedDate,
			dayParam,
			jsonLd: [
				{
					'@context': 'https://schema.org',
					'@type': 'WebPage',
					name: 'UW-Madison Campus Map',
					description: 'Interactive campus map showing building occupancy and student movement patterns',
					url: `https://uwcourses.com/campus?day=${dayParam}`
				}
			]
		};
	} catch (err) {
		console.error('Error loading campus data:', err);
		throw error(500, 'Failed to load campus data');
	}
};