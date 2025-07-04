import { env } from '$env/dynamic/public';
import { error } from '@sveltejs/kit';

export const load = async ({ fetch }) => {
	try {
		// Format today's date for API
		const today = new Date();
		const month = String(today.getMonth() + 1).padStart(2, '0');
		const day = String(today.getDate()).padStart(2, '0');
		const year = String(today.getFullYear()).slice(-2);
		const todayDateStr = `${month}-${day}-${year}`;

		// Load trips data and today's highlights data in parallel
		const [tripsResponse, highlightsResponse] = await Promise.all([
			fetch(`${env.PUBLIC_API_URL}/trips.json`),
			fetch(`https://static.uwcourses.com/meetings/${todayDateStr}.geojson`)
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
			console.warn('Failed to load highlights data for today:', highlightsResponse.statusText);
		}

		return {
			subtitle: 'Campus Map',
			description: 'Interactive campus map showing building occupancy and student movement patterns',
			tripsData,
			highlightsData,
			initialDate: today,
			jsonLd: [
				{
					'@context': 'https://schema.org',
					'@type': 'WebPage',
					name: 'UW-Madison Campus Map',
					description: 'Interactive campus map showing building occupancy and student movement patterns',
					url: 'https://uwcourses.com/campus'
				}
			]
		};
	} catch (err) {
		console.error('Error loading campus data:', err);
		throw error(500, 'Failed to load campus data');
	}
};