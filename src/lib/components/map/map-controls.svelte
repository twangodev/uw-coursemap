<script lang="ts">
	import { Slider } from '$lib/components/ui/slider';
	import { Calendar } from '$lib/components/ui/calendar';
	import { Popover, PopoverContent, PopoverTrigger } from '$lib/components/ui/popover';
	import { getLocalTimeZone, today } from '@internationalized/date';

	// Props
	interface Props {
		timeIndex: number;
		metadata: any;
		isPlaying: boolean;
		onTimeIndexChange: (index: number) => void;
		onTogglePlay: () => void;
		onDateChange: (date: Date) => void;
	}

	let {
		timeIndex = $bindable(),
		metadata,
		isPlaying,
		onTimeIndexChange,
		onTogglePlay,
		onDateChange
	}: Props = $props();

	let selectedDate = $state(today(getLocalTimeZone()));
	let calendarOpen = $state(false);

	function formatDateTime(timeIndex: number): {
		time: string;
		date: string;
		timezone: string;
		hour: number;
		minute: number;
	} {
		if (!metadata) return { time: '--:--', date: '--/--', timezone: '', hour: 0, minute: 0 };

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
			date: date.toLocaleDateString('en-US', {
				month: 'short',
				day: 'numeric'
			}),
			timezone: date.toLocaleTimeString('en-US', {
				timeZoneName: 'short'
			}).split(' ').pop() || '',
			hour: date.getHours() % 12 || 12,
			minute: date.getMinutes()
		};
	}

	function getCurrentStats(timeIndex: number) {
		if (!metadata) return { persons: 0, instructors: 0 };

		return {
			persons: metadata.total_persons?.[timeIndex] || 0,
			instructors: metadata.total_instructors?.[timeIndex] || 0
		};
	}

	function handleDateChange(value: any) {
		if (value) {
			const newDate = new Date(value.year, value.month - 1, value.day);
			onDateChange(newDate);
			calendarOpen = false;
		}
	}
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

	<!-- Time and Date with Calendar Popover -->
	<div class="flex flex-col items-center min-w-20">
		<div class="text-white font-mono text-sm">
			{formatDateTime(timeIndex).time}
		</div>
		<Popover bind:open={calendarOpen}>
			<PopoverTrigger>
				<button
					class="text-gray-300 text-xs hover:text-white transition-colors cursor-pointer"
				>
					{formatDateTime(timeIndex).date}
				</button>
			</PopoverTrigger>
			<PopoverContent class="w-auto p-4" align="center" side="top">
				<Calendar
					type="single"
					bind:value={selectedDate}
					captionLayout="dropdown"
					onValueChange={handleDateChange}
				/>
				<div class="text-center mt-3 pt-3 border-t">
					<p class="text-xs text-muted-foreground">
						All times displayed in {Intl.DateTimeFormat().resolvedOptions().timeZone}
					</p>
				</div>
			</PopoverContent>
		</Popover>
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
				{getCurrentStats(timeIndex).persons.toLocaleString()}
			</div>
			<div class="text-gray-400">Persons</div>
		</div>
		<div class="flex flex-col items-center">
			<div class="text-green-300 font-semibold">
				{getCurrentStats(timeIndex).instructors.toLocaleString()}
			</div>
			<div class="text-gray-400">Instructors</div>
		</div>
	</div>
</div>