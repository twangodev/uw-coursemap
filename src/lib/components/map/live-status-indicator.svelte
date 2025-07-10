<script lang="ts">
	import {
		Tooltip,
		TooltipContent,
		TooltipProvider,
		TooltipTrigger,
	} from "$lib/components/ui/tooltip/index.js";

	// Props
	interface Props {
		timeIndex: number;
		metadata: any;
		isManualControl?: boolean;
	}

	let { timeIndex, metadata, isManualControl = false }: Props = $props();

	function getLiveStatus(timeIndex: number): {
		isLive: boolean;
		tooltip: string;
	} {
		if (isManualControl) {
			return {
				isLive: false,
				tooltip: 'Manual time control - not following live time'
			};
		}

		if (!metadata?.start_time) {
			return {
				isLive: false,
				tooltip: 'Time data unavailable'
			};
		}

		const now = Date.now();
		const currentTimestamp = metadata.start_time + timeIndex * (metadata.chunk_duration_minutes || 5) * 60 * 1000;
		const endTime = metadata.start_time + ((metadata.total_chunks || 192) * (metadata.chunk_duration_minutes || 5) * 60 * 1000);

		// Check if current real time is within the data window
		const isInBounds = now >= metadata.start_time && now <= endTime;
		
		if (!isInBounds) {
			return {
				isLive: false,
				tooltip: 'Live time is outside the data window'
			};
		}

		// Check if we're within a reasonable range of live time (±5 minutes)
		const timeDiff = Math.abs(now - currentTimestamp);
		const liveThreshold = 5 * 60 * 1000; // 5 minutes in milliseconds
		
		if (timeDiff <= liveThreshold) {
			return {
				isLive: true,
				tooltip: 'Following live time'
			};
		} else {
			return {
				isLive: false,
				tooltip: 'Not following live time'
			};
		}
	}

	let liveStatus = $derived(getLiveStatus(timeIndex));
</script>

<TooltipProvider>
	<Tooltip>
		<TooltipTrigger>
			<div 
				class="relative"
				role="status"
				aria-live="polite"
				aria-label={liveStatus.tooltip}
			>
				<div class="relative">
					{#if liveStatus.isLive}
						<div class="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
						<div class="absolute top-0 left-0 w-2 h-2 bg-green-400 rounded-full animate-ping"></div>
					{:else}
						<div class="w-2 h-2 bg-yellow-400 rounded-full"></div>
					{/if}
				</div>
			</div>
		</TooltipTrigger>
		<TooltipContent>
			<p>{liveStatus.tooltip}</p>
		</TooltipContent>
	</Tooltip>
</TooltipProvider>