<script lang="ts">
	import Map from '$lib/components/map/map.svelte';
	import MapControls from '$lib/components/map/map-controls.svelte';
	import { env } from '$env/dynamic/public';

	let timeIndex = $state(0);
	let metadata = $state<any>(null);
	let isPlaying = $state(false);
	let playInterval: NodeJS.Timeout | null = null;
	let selectedJSDate = $state(new Date());
	let highlightsData = $state<any>(null);
	let tripsData = $state<any>(null);

	function formatDateForAPI(date: Date): string {
		const month = String(date.getMonth() + 1).padStart(2, '0');
		const day = String(date.getDate()).padStart(2, '0');
		const year = String(date.getFullYear()).slice(-2);
		return `${month}-${day}-${year}`;
	}

	function generateHighlightsUrl(date: Date): string {
		const dateStr = formatDateForAPI(date);
		return `https://static.uwcourses.com/meetings/${dateStr}.geojson`;
	}

	let highlightsUrl = $derived(generateHighlightsUrl(selectedJSDate));

	// Load highlights data
	async function loadHighlightsData(url: string) {
		try {
			const response = await fetch(url);
			const data = await response.json();
			highlightsData = data;
			// Extract metadata for controls
			metadata = data.metadata;
		} catch (error) {
			console.warn('Failed to load highlights data:', error);
		}
	}

	// Load trips data
	async function loadTripsData() {
		try {
			const response = await fetch(`${env.PUBLIC_API_URL}/trips.json`);
			const data = await response.json();
			tripsData = data;
		} catch (error) {
			console.warn('Failed to load trips data:', error);
		}
	}

	function handleTimeIndexChange(index: number) {
		// This could trigger re-rendering if needed
		console.log('Time index changed to:', index);
	}

	function handleTogglePlay() {
		if (isPlaying) {
			if (playInterval) {
				clearInterval(playInterval);
				playInterval = null;
			}
			isPlaying = false;
		} else {
			isPlaying = true;
			playInterval = setInterval(() => {
				if (timeIndex >= ((metadata?.total_chunks ?? 192) - 1)) {
					timeIndex = 0;
				} else {
					timeIndex += 1;
				}
			}, 250);
		}
	}

	function handleDateChange(newDate: Date) {
		selectedJSDate = newDate;
		timeIndex = 0;
		isPlaying = false;
		if (playInterval) {
			clearInterval(playInterval);
			playInterval = null;
		}
	}

	// Load trips data on mount
	$effect(() => {
		loadTripsData();
	});

	// Load highlights data when URL changes
	$effect(() => {
		loadHighlightsData(highlightsUrl);
	});
</script>

<Map {highlightsData} {tripsData} {timeIndex}>
	<MapControls
		bind:timeIndex
		{metadata}
		{isPlaying}
		onTimeIndexChange={handleTimeIndexChange}
		onTogglePlay={handleTogglePlay}
		onDateChange={handleDateChange}
	/>
</Map>