<script lang="ts">
	import Map from '$lib/components/map/map.svelte';

	function formatDateForAPI(date: Date): string {
		const month = String(date.getMonth() + 1).padStart(2, '0');
		const day = String(date.getDate()).padStart(2, '0');
		const year = String(date.getFullYear()).slice(-2);
		return `${month}-${day}-${year}`;
	}

	// Generate building highlights URL with date placeholder
	const buildingHighlightsUrl = 'https://static.uwcourses.com/meetings/{date}.geojson'
</script>

<Map {buildingHighlightsUrl} showTrips={true} showControls={true} />