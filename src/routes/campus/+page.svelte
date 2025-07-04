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

	// Calculate current timestamp from timeIndex and metadata
	let currentTime = $derived(() => {
		if (!metadata?.start_time) {
			return Date.now(); // Fallback to current time if no metadata
		}
		
		// Calculate timestamp from timeIndex (timeIndex is now properly initialized)
		const chunkDurationMs = (metadata.chunk_duration_minutes || 5) * 60 * 1000;
		return metadata.start_time + (timeIndex * chunkDurationMs);
	});

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
			
			// Initialize timeIndex based on real current time when metadata is first loaded
			if (metadata?.start_time && timeIndex === 0) {
				const now = Date.now();
				const start_time = metadata.start_time;
				const chunkDurationMs = (metadata.chunk_duration_minutes || 5) * 60 * 1000;
				const totalChunks = metadata.total_chunks || 192;
				const end_time = start_time + (totalChunks * chunkDurationMs);
				
				// Calculate timeIndex from clamped current time
				let clampedTime = now;
				if (now < start_time) {
					clampedTime = start_time;
				} else if (now > end_time) {
					clampedTime = end_time;
				}
				
				// Convert clamped time to timeIndex
				timeIndex = Math.floor((clampedTime - start_time) / chunkDurationMs);
			}
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

<Map {highlightsData} {tripsData} currentTime={currentTime()}>
	<MapControls
		bind:timeIndex
		{metadata}
		{isPlaying}
		onTimeIndexChange={handleTimeIndexChange}
		onTogglePlay={handleTogglePlay}
		onDateChange={handleDateChange}
	/>
</Map>