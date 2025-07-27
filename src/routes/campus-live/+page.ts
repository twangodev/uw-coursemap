import { env } from '$env/dynamic/public';
import { error } from '@sveltejs/kit';
import { formatDateForAPI } from '$lib/utils/campus-date-validation.js';

export const load = async ({ fetch }) => {
	// Always use today's date
	const today = new Date();
	const todayParam = formatDateForAPI(today);

	try {
		// Load today's highlights data (trips data removed)
		const highlightsResponse = await fetch(`${env.PUBLIC_API_URL}/meetings/${todayParam}.geojson`);

		// Handle highlights data - if no data for today, just return null
		let highlightsData = null;
		if (highlightsResponse.ok) {
			highlightsData = await highlightsResponse.json();
		} else {
			console.info(`No highlights data available for today (${todayParam})`);
		}

		return {
			subtitle: 'Campus Map',
			description: 'Interactive campus map showing current building occupancy',
			highlightsData,
			selectedDate: today,
			dayParam: todayParam,
			jsonLd: [
				{
					'@context': 'https://schema.org',
					'@type': 'WebPage',
					name: 'UW-Madison Campus Map',
					description: 'Interactive campus map showing current building occupancy',
					url: 'https://uwcourses.com/campus'
				}
			]
		};
	} catch (err) {
		console.error('Error loading campus data:', err);
		throw error(500, 'Failed to load campus data');
	}
};