<script lang="ts">
	import Map from '$lib/components/map/map.svelte';
	import MapControls from '$lib/components/map/map-controls.svelte';
	import { goto } from '$app/navigation';

	// Props from load function
	interface Props {
		data: {
			highlightsData: any;
			selectedDate: Date;
			dayParam: string;
		};
	}

	let { data }: Props = $props();

	// Component state
	let timeIndex = $state(0);
	let metadata = $state<any>(data.highlightsData?.metadata || null);
	let isPlaying = $state(false);
	let isManualControl = $state(false);
	let playInterval: NodeJS.Timeout | null = null;
	let highlightsData = $state<any>(data.highlightsData);

	// Calculate current timestamp from timeIndex and metadata
	let currentTime = $derived(() => {
		if (!metadata?.start_time) {
			return Date.now(); // Fallback to current time if no metadata
		}
		
		// Calculate timestamp from timeIndex (timeIndex is now properly initialized)
		const chunkDurationMs = (metadata.chunk_duration_minutes || 5) * 60 * 1000;
		return metadata.start_time + (timeIndex * chunkDurationMs);
	});

	function handleTimeIndexChange(index: number) {
		// Mark as manual control when user changes time
		isManualControl = true;
	}

	function handleTogglePlay() {
		if (isPlaying) {
			if (playInterval) {
				clearInterval(playInterval);
				playInterval = null;
			}
			isPlaying = false;
		} else {
			// Mark as manual control when user manually plays
			isManualControl = true;
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

	// Sync component state with new data
	$effect(() => {
		highlightsData = data.highlightsData;
		metadata = data.highlightsData?.metadata || null;
		
		// Reset time controls when data changes
		timeIndex = 0;
		isPlaying = false;
		isManualControl = false; 
		if (playInterval) {
			clearInterval(playInterval);
			playInterval = null;
		}
	});

	// Initialize timeIndex based on real current time when metadata is available
	$effect(() => {
		if (metadata?.start_time && timeIndex === 0 && !isManualControl) {
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
	});

</script>

<Map {highlightsData} currentTime={currentTime()}>
	<MapControls
		bind:timeIndex
		{metadata}
		{isPlaying}
		{isManualControl}
		onTimeIndexChange={handleTimeIndexChange}
		onTogglePlay={handleTogglePlay}
	/>
</Map>