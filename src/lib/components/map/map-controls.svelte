<script lang="ts">
	import { Slider } from '$lib/components/ui/slider';
	import LiveStatusIndicator from './live-status-indicator.svelte';

	// Props
	interface Props {
		timeIndex: number;
		metadata: any;
		isPlaying: boolean;
		isManualControl?: boolean;
		onTimeIndexChange: (index: number) => void;
		onTogglePlay: () => void;
	}

	let {
		timeIndex = $bindable(),
		metadata,
		isPlaying,
		isManualControl = false,
		onTimeIndexChange,
		onTogglePlay
	}: Props = $props();

	function formatDateTime(timeIndex: number): {
		time: string;
		date: string;
		timezone: string;
		hour: number;
		minute: number;
	} {
		// Always show today's date, regardless of metadata
		const today = new Date();
		
		if (!metadata) {
			return { 
				time: '--:--', 
				date: today.toLocaleDateString('en-US', {
					month: 'short',
					day: 'numeric'
				}), 
				timezone: today.toLocaleTimeString('en-US', {
					timeZoneName: 'short'
				}).split(' ').pop() || '', 
				hour: 0, 
				minute: 0 
			};
		}

		const startTime = metadata.start_time;
		const chunkDuration = metadata.chunk_duration_minutes;
		const currentTimestamp = startTime + timeIndex * chunkDuration * 60 * 1000;
		const date = new Date(currentTimestamp);

		return {
			time: date.toLocaleTimeString('en-US', {
				hour: '2-digit',
				minute: '2-digit',
				hour12: true
			}),
			date: today.toLocaleDateString('en-US', {
				month: 'short',
				day: 'numeric'
			}),
			timezone: today.toLocaleTimeString('en-US', {
				timeZoneName: 'short'
			}).split(' ').pop() || '',
			hour: date.getHours() % 12 || 12,
			minute: date.getMinutes()
		};
	}

	// Make stats reactive to both timeIndex and metadata changes
	let currentStats = $derived(() => {
		if (!metadata) return { persons: 0, instructors: 0 };

		return {
			persons: metadata.total_persons?.[timeIndex] || 0,
			instructors: metadata.total_instructors?.[timeIndex] || 0
		};
	});
</script>

<!-- Video-style control bar -->
<div
	class="absolute bottom-6 left-1/2 transform -translate-x-1/2 bg-black/60 backdrop-blur-md rounded-full px-6 py-3 flex items-center gap-4 pointer-events-auto"
>
	<!-- Play Button -->
	<button
		onclick={onTogglePlay}
		class="flex items-center justify-center w-8 h-8 rounded-full bg-white/20 hover:bg-white/30 transition-colors"
	>
		{#if isPlaying}
			<!-- Pause icon -->
			<svg class="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 24 24">
				<path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
			</svg>
		{:else}
			<!-- Play icon -->
			<svg class="w-4 h-4 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24">
				<path d="M8 5v14l11-7z" />
			</svg>
		{/if}
	</button>

	<!-- Time and Date Display (no longer clickable) -->
	<div class="flex flex-col items-center min-w-20">
		<div class="text-white font-mono text-sm">
			{formatDateTime(timeIndex).time}
		</div>
		<div class="text-gray-300 text-xs flex items-center gap-2">
			<LiveStatusIndicator 
				{timeIndex}
				{metadata}
				{isManualControl}
			/>
			{formatDateTime(timeIndex).date}
		</div>
	</div>

	<!-- Slider -->
	<div class="flex-1 min-w-64">
		<Slider
			type="single"
			bind:value={timeIndex}
			max={(metadata?.total_chunks ?? 192) - 1}
			onValueChange={() => onTimeIndexChange(timeIndex)}
		/>
	</div>

	<!-- Statistics -->
	<div class="flex gap-4 text-xs">
		<div class="flex flex-col items-center">
			<div class="text-blue-300 font-semibold">
				{currentStats().persons.toLocaleString()}
			</div>
			<div class="text-gray-400">Persons</div>
		</div>
		<div class="flex flex-col items-center">
			<div class="text-green-300 font-semibold">
				{currentStats().instructors.toLocaleString()}
			</div>
			<div class="text-gray-400">Instructors</div>
		</div>
	</div>
</div>