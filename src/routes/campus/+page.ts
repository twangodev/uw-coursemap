import { env } from '$env/dynamic/public';
import { error, redirect } from '@sveltejs/kit';
import {
	fetchAvailableDates,
	validateDateParam,
	formatDateForAPI
} from '$lib/utils/campus-date-validation.js';

export const load = async ({ fetch, url }) => {
	const dayParam = url.searchParams.get('day');
	
	// Fetch available dates and validate the requested date
	const availableDates = await fetchAvailableDates(fetch);
	const validation = validateDateParam(dayParam, availableDates);
	
	// Redirect if date is invalid or unavailable
	if (!validation.isValid && validation.redirectDate) {
		throw redirect(302, `/campus?day=${validation.redirectDate}`);
	}

	try {
		// At this point, dayParam is the final validated date string
		const finalDateStr = dayParam || formatDateForAPI(new Date());
		
		// Load trips data and selected date's highlights data in parallel
		const [tripsResponse, highlightsResponse] = await Promise.all([
			fetch(`${env.PUBLIC_API_URL}/trips.json`),
			fetch(`${env.PUBLIC_API_URL}/meetings/${finalDateStr}.geojson`)
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
			console.warn(`Failed to load highlights data for ${finalDateStr}:`, highlightsResponse.statusText);
		}

		return {
			subtitle: 'Campus Map',
			description: 'Interactive campus map showing building occupancy and student movement patterns',
			tripsData,
			highlightsData,
			selectedDate: validation.selectedDate,
			dayParam: finalDateStr,
			availableDates,
			jsonLd: [
				{
					'@context': 'https://schema.org',
					'@type': 'WebPage',
					name: 'UW-Madison Campus Map',
					description: 'Interactive campus map showing building occupancy and student movement patterns',
					url: `https://uwcourses.com/campus?day=${finalDateStr}`
				}
			]
		};
	} catch (err) {
		console.error('Error loading campus data:', err);
		throw error(500, 'Failed to load campus data');
	}
};